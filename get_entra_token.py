import os
import requests
import urllib.parse
from dotenv import load_dotenv

load_dotenv() 

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
# The audience configured in GCP Workload Identity Provider
AUDIENCE = os.getenv("AUDIENCE")

token_url = f"https://login.microsoftonline.com/4eba731f-838b-440d-8168-3f03905ee87d/oauth2/v2.0/token"

payload = {
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "scope": f"{AUDIENCE}/.default openid"
}

response = requests.post(token_url, data=payload)
response.raise_for_status()

# Print the raw access/ID token to stdout for Google's WIF process to consume
print(response.json())