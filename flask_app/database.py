import os
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase only once
if not firebase_admin._apps:
    cred_path = os.getenv("FIREBASE_CREDENTIALS")
    if not cred_path:
        raise RuntimeError(
            "FIREBASE_CREDENTIALS environment variable not set"
        )

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()


def add(id, user_name, data, agent):
    doc_ref = db.collection(user_name).document(agent)
    doc_ref.set(data)
    return f"Response saved successfully with id-{id}"

