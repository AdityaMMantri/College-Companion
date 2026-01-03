import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate('./project.json')
app = firebase_admin.initialize_app(cred)
db = firestore.client()

doc_ref = db.collection("users").document("aturing")
doc_ref.set({"first": "Alan", "middle": "Mathison", "last": "Turing", "born": 1912})

def add(id,user_name,data,agent):
    doc_ref = db.collection(user_name).document(agent)
    doc_ref.set(data)
    return f"Response saved successfully with id-{id}"


