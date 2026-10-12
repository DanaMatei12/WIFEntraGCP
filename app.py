
import os
import identity
import identity.web
import requests
import json
import google.auth
import google.auth.transport.requests
from google.cloud import bigquery
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
from dotenv import load_dotenv

load_dotenv() 

# 1. Fetch the Application Default Credentials (ADC)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\\RandD\\VertexConWIF\\clientLibraryConfig-vertexconpocprovider.json"
credentials, project = google.auth.default(
    scopes=['https://www.googleapis.com/auth/cloud-platform']
)

# 2. Refresh the credentials to populate the access token
auth_request = google.auth.transport.requests.Request()
#credentials.refresh(auth_request)

try:
    credentials.refresh(auth_request)
except RefreshError as e:
    print(f"Failed to exchange token: {e}")

import app_config

app = Flask(__name__)
app.config.from_object(app_config)
Session(app)

# This section is needed for url_for("foo", _external=True) to automatically
# generate http scheme when this sample is running on localhost,
# and to generate https scheme when it is deployed behind reversed proxy.
# See also https://flask.palletsprojects.com/en/2.2.x/deploying/proxy_fix/
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

auth = identity.web.Auth(
    session=session,
    authority=app.config.get("AUTHORITY"),
    client_id=app.config["CLIENT_ID"],
    client_credential=app.config["CLIENT_SECRET"],
)


@app.route("/login")
def login():
    return render_template("login.html", version=identity.__version__, **auth.log_in(
        scopes=app_config.SCOPE, # Have user consent to scopes during log-in
        #redirect_uri=url_for("auth_response", _external=True), # Optional. If present, this absolute URL must match your app's redirect_uri registered in Azure Portal
        redirect_uri="http://localhost:5000/getAToken" # hack
        ))


@app.route(app_config.REDIRECT_PATH)
def auth_response():
    result = auth.complete_log_in(request.args)
    if "error" in result:
        return render_template("auth_error.html", result=result)
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    return redirect(auth.log_out(url_for("index", _external=True)))


@app.route("/")
def index():
    if not (app.config["CLIENT_ID"] and app.config["CLIENT_SECRET"]):
        # This check is not strictly necessary.
        # You can remove this check from your production code.
        return render_template('config_error.html')
    if not auth.get_user():
        return redirect(url_for("login"))
    return render_template('index.html', user=auth.get_user(), version=identity.__version__)


@app.route("/call_downstream_api")
def call_downstream_api():
    # Use access token to call downstream api
    token = auth.get_token_for_user(app_config.SCOPE)
    if "error" in token:
        return redirect(url_for("login"))
    
    api_result = {}
    QUERY = 'select * from dataset.testtable limit 10'

    try:
        # The client automatically handles HTTP connections under the hood
        client = bigquery.Client()
        query_job = client.query(QUERY)
        
        # Fetches results from the API
        records = [dict(row) for row in query_job]
        api_result = json.dumps(str(records))   
    
    except RefreshError as e:
        print(f"Failed to connect to BigQuery: {e}")

    return render_template('display.html', result=api_result)


if __name__ == "__main__":
    app.run(debug=True)
