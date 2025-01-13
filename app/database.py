from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["payment_db"]

def create_database():
    db.payments.create_index("payee_due_date")
