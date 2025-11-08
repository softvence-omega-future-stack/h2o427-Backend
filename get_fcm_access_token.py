import os
from background_check.settings import BASE_DIR
from google.oauth2 import service_account
import google.auth.transport.requests


# Path to your Firebase service account JSON key
SERVICE_ACCOUNT_FILE = os.getenv('FIREBASE_CREDENTIALS_PATH', BASE_DIR / 'firebase-credentials.json')


def generate_fcm_access_token():
    """Generate and print an OAuth 2.0 access token for Firebase Cloud Messaging."""
    # Load credentials from the service account key
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/firebase.messaging"],
    )

    # Refresh to get a valid access token
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)

    # Print the access token
    print("Your Firebase Access Token:\n")
    print(credentials.token)
    print("\nExpires at:", credentials.expiry)

if __name__ == "__main__":
    generate_fcm_access_token()
