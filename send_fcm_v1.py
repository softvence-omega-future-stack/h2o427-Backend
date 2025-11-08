import json
import os
import requests
from google.oauth2 import service_account
import google.auth.transport.requests

from background_check.settings import BASE_DIR


SERVICE_ACCOUNT_FILE = os.getenv('FIREBASE_CREDENTIALS_PATH', BASE_DIR / 'firebase-credentials.json')

PROJECT_ID = "h2o427-918db"

DEVICE_TOKEN = "cvF30bCQQOWhd3ZDzdikrl:APA91bFTeDckJySEQ989h7r2Fb8WCFl8j2LejX8MEUjYuVJv0xsX-UIhhmjCCV0q3yaxL9ZaWJ7YiePLVGOHZW1QageWJaZnVIx0-MvPS2q_2xzWMyaCbsI"

def get_access_token():
    """Generate a valid OAuth2 access token using a service account key."""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/firebase.messaging"],
    )
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    return credentials.token

# === SEND MESSAGE ===
def send_fcm_message():
    access_token = get_access_token()
    url = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; UTF-8",
    }

    # The message payload
    message = {
        "message": {
            "token": DEVICE_TOKEN,
            "notification": {
                "title": "Hello!",
                "body": "This is sent using FCM HTTP v1 API from Python"
            }
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(message))
    print("Status Code:", response.status_code)
    print("Response:", response.text)

# === RUN ===
if __name__ == "__main__":
    send_fcm_message()
