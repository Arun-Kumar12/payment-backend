import os
from fastapi import UploadFile
from app.database import db
import pandas as pd

def normalize_csv_and_save_to_db(file_path: str):
    
    df = pd.read_csv(file_path)

    df["payee_first_name"] = df["payee_first_name"].astype(str)
    df["payee_last_name"] = df["payee_last_name"].astype(str)
    df["payee_payment_status"] = df["payee_payment_status"].astype(str)
    df["payee_added_date_utc"] = pd.to_datetime(df["payee_added_date_utc"]).astype(int) // 10**9
    df["payee_due_date"] = pd.to_datetime(df["payee_due_date"]).dt.strftime("%Y-%m-%d")
    df["payee_city"] = df["payee_city"].astype(str)
    df["payee_country"] = df["payee_country"].str.upper()
    df["currency"] = df["currency"].str.upper()
    df["discount_percent"] = df["discount_percent"].fillna(0).round(2)
    df["tax_percent"] = df["tax_percent"].fillna(0).round(2)
    df["due_amount"] = df["due_amount"].round(2)
    df["total_due"] = (
        df["due_amount"] * (1 + (df["tax_percent"] / 100)) * (1 - (df["discount_percent"] / 100))
    ).round(2)

    records = df.to_dict("records")
    db.payments.insert_many(records)

    return f"{len(records)} records normalized and saved to MongoDB successfully!"
