import firebase_admin
from firebase_admin import credentials, firestore

# Initialise Firebase
cred = credentials.Certificate("../maps-82be0-firebase-adminsdk-fbsvc-0860dab1b8.json")
firebase_admin.initialize_app(cred)

# Get Firebase datastore reference
db = firestore.client()


def add_allocation(country_id, value):
    """Add an allocation record to Firestore."""
    db.collection('allocations').add({
        'country_id': country_id,
        'value': value,
        'created_at': firestore.SERVER_TIMESTAMP
    })