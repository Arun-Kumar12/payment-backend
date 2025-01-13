from fastapi import APIRouter, HTTPException, UploadFile, Form
from app.database import db
from app.models import PaymentModel
from datetime import datetime
from bson import ObjectId
import os
from fastapi.responses import FileResponse

router = APIRouter(prefix="/payments", tags=["Payments"])

UPLOAD_FOLDER = "app/uploads/evidence_files"
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}


def is_allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@router.get("/")
async def get_payments(
    skip: int = 0,
    limit: int = 10,
    status: str = None,
    payeeName: str = None,
    payeeAddressLine1: str = None,
    payeeCity: str = None,
    payeeCountry: str = None,
    payeeProvinceOrState: str = None,
    payeePostalCode: str = None,
    payeePhoneNumber: str = None,
    payeeEmail: str = None,
    currency: str = None
):
    query = {}

    if status:
        query["payee_payment_status"] = {"$regex": status, "$options": "i"}
    
    if payeeName:
        query["$or"] = [
            {"payee_first_name": {"$regex": payeeName, "$options": "i"}},
            {"payee_last_name": {"$regex": payeeName, "$options": "i"}}
        ]
    
    if payeeAddressLine1:
        query["payee_address_line_1"] = {"$regex": payeeAddressLine1, "$options": "i"}
    
    if payeeCity:
        query["payee_city"] = {"$regex": payeeCity, "$options": "i"}
    
    if payeeCountry:
        query["payee_country"] = {"$regex": payeeCountry, "$options": "i"}
    
    if payeeProvinceOrState:
        query["payee_province_or_state"] = {"$regex": payeeProvinceOrState, "$options": "i"}
    
    if payeePostalCode:
        query["payee_postal_code"] = {"$regex": payeePostalCode, "$options": "i"}
    
    if payeePhoneNumber:
        query["payee_phone_number"] = {"$regex": payeePhoneNumber, "$options": "i"}
    
    if payeeEmail:
        query["payee_email"] = {"$regex": payeeEmail, "$options": "i"}
    
    if currency:
        query["currency"] = {"$regex": currency, "$options": "i"}

    total = db.payments.count_documents(query)
    payments = list(db.payments.find(query).skip(skip).limit(limit))

    today = datetime.utcnow()

    for payment in payments:
        payment["_id"] = str(payment["_id"])

        if isinstance(payment["payee_due_date"], str):
            payment_due_date = datetime.fromisoformat(payment["payee_due_date"])
        else:
            payment_due_date = payment["payee_due_date"]

        if payment["payee_payment_status"] != 'completed':
            if payment_due_date.date() == today.date():
                payment["payee_payment_status"] = "due_now"
            elif payment_due_date < today:
                payment["payee_payment_status"] = "overdue"

        discount = payment.get("discount_percent", 0.0) / 100
        tax = payment.get("tax_percent", 0.0) / 100
        due_amount = payment["due_amount"]

        payment["total_due"] = round(due_amount * (1 + tax) * (1 - discount), 2)
    
    return {"data": payments, "total": total}

@router.get("/{payment_id}")
async def get_payment_by_id(payment_id: str):
    try:
        object_id = ObjectId(payment_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payment ID format")
    
    payment = db.payments.find_one({"_id": object_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment["_id"] = str(payment["_id"])
    
    if isinstance(payment["payee_due_date"], str):
        payment_due_date = datetime.fromisoformat(payment["payee_due_date"])
    else:
        payment_due_date = payment["payee_due_date"]

    today = datetime.utcnow()

    if payment["payee_payment_status"] != 'completed':
        if payment_due_date.date() == today.date():
            payment["payee_payment_status"] = "due_now"
        elif payment_due_date < today:
            payment["payee_payment_status"] = "overdue"

    discount = payment.get("discount_percent", 0.0) / 100
    tax = payment.get("tax_percent", 0.0) / 100
    due_amount = payment["due_amount"]

    payment["total_due"] = round(due_amount * (1 + tax) * (1 - discount), 2)
    return {"data": payment}

@router.post("/")
async def add_payment(payment: PaymentModel):
    try:
        total_due = payment.due_amount + (payment.due_amount * (payment.tax_percent / 100)) - (
            payment.due_amount * (payment.discount_percent / 100)
        )
        payment_dict = payment.dict()
        payment_dict["total_due"] = round(total_due, 2)
        
        result = db.payments.insert_one(payment_dict)
        return {"id": str(result.inserted_id), "message": "Payment added successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.delete("/{payment_id}")
async def delete_payment(payment_id: str):
    try:
        object_id = ObjectId(payment_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payment ID format")
    
    result = db.payments.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return {"message": "Payment deleted successfully"}

@router.put("/{payment_id}/update")
async def update_payment(
    payment_id: str,
    due_date: str = Form(...),
    due_amount: float = Form(...),
    status: str = Form(...),
    file: UploadFile = None
):
    try:
        object_id = ObjectId(payment_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payment ID format")
    
    payment = db.payments.find_one({"_id": object_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if status == "completed":
        if not file:
            raise HTTPException(
                status_code=400,
                detail="Evidence file is required when marking status as 'completed'"
            )
        
        if not is_allowed_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail="Evidence file must be a PDF, PNG, JPG, or JPEG"
            )
        
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        filename = f"{payment_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        try:
            with open(file_path, "wb") as f:
                f.write(file.file.read())
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}"
            )
        
        # Store the relative path instead of the full path
        payment["evidence_file_path"] = f"evidence_files/{filename}"
    
    payment["payee_due_date"] = due_date
    payment["due_amount"] = due_amount
    payment["payee_payment_status"] = status

    update_data = {
        "payee_due_date": due_date,
        "due_amount": due_amount,
        "payee_payment_status": status,
    }

    if "evidence_file_path" in payment:
        update_data["evidence_file_path"] = payment["evidence_file_path"]

    db.payments.update_one({"_id": object_id}, {"$set": update_data})
    
    return {"message": "Payment updated successfully"}