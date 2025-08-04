import os
import json
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv

load_dotenv()

firebase_json_str = os.getenv("FIREBASE_JSON_STRING")

if firebase_json_str:
    # Convert the string back to a dictionary
    firebase_data = json.loads(firebase_json_str)

    # Create a temporary file for the credential
    with open("firebase_temp.json", "w") as f:
        json.dump(firebase_data, f)

    # Initialize Firebase with that temp file
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase_temp.json")
        firebase_admin.initialize_app(cred)
else:
    raise ValueError("FIREBASE_JSON_STRING not found in environment variables")

# import os
# import firebase_admin
# from firebase_admin import credentials
# from dotenv import load_dotenv

# load_dotenv()

# FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase.json")

# if not firebase_admin._apps:
#     cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
#     firebase_admin.initialize_app(cred)
