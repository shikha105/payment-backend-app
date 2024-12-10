from fastapi import APIRouter, HTTPException, Query
from config.mongodb import payments_collection, files_collection
from models.payment import Payment
from datetime import date, datetime
from utils import convert_date_to_datetime, convert_to_date, convert_objectid_to_str,convert_str_to_objectid
from services.payment_service import calculate_total_due

router = APIRouter()
# Get all payments
@router.get("/payments/")
async def get_payments(search: str = None, page: int = 1, limit: int = 10):
    query = {}
    if search:
        query["$or"] = [
            {"payee_first_name": {"$regex": search, "$options": "i"}},
            {"payee_last_name": {"$regex": search, "$options": "i"}},
        ]

    today = date.today()
    payments_cursor = payments_collection.find(query)
    payments = await payments_cursor.to_list(length=limit * page)

    response = []
    total_due_amount = 0 
    for payment in payments:
        total_due_amount = await calculate_total_due(payment)
        payment = convert_objectid_to_str(payment)
        payment["payee_due_date"] = convert_to_date(payment["payee_due_date"])

        if payment["payee_due_date"] < today:
            payment["payee_payment_status"] = "overdue"
        elif payment["payee_due_date"] == today:
            payment["payee_payment_status"] = "due_now"

        # Map evidence ID for the payment
        payment["evidence_id"] = payment.get("evidence_id")

        payment["payee_due_date"] = convert_date_to_datetime(payment["payee_due_date"])
        response.append(payment)

    total_payments = await payments_collection.count_documents(query)
    total_due = total_payments * total_due_amount
    total_due = round(total_due, 2)
    paginated = response[(page - 1) * limit : page * limit]

    return {"data": paginated, "total": total_due}

# Fetch a single payment by ID
@router.get("/payments/{payment_id}")
async def get_payment_by_id(payment_id: str):
    payment_id_obj = convert_str_to_objectid(payment_id)
    
    payment = await payments_collection.find_one({"_id": payment_id_obj})
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment = convert_objectid_to_str(payment)
   
    payment["payee_due_date"] = convert_to_date(payment["payee_due_date"])
    payment["evidence_id"] = payment.get("evidence_id")
    return {"data": payment}

# Create a new payment
@router.post("/payments/")
async def create_payment(payment: Payment):
    if payment.payee_payment_status != "pending":
        raise HTTPException(
            status_code=400,
            detail="payee_payment_status must be 'pending' when creating a payment",
        )

    if payment.evidence_id:
        evidence_id_obj = convert_str_to_objectid(payment.evidence_id)
        evidence = await files_collection.find_one({"_id": evidence_id_obj})
        if not evidence:
            raise HTTPException(
                status_code=404, detail="Evidence file not found for the given ID"
            )

    payment.payee_due_date = convert_date_to_datetime(payment.payee_due_date)
    result = await payments_collection.insert_one(payment.dict())
    return {"id": str(result.inserted_id)}



@router.put("/payments/{payment_id}")
async def update_payment(payment_id: str, payment: Payment):
    valid_payment_statuses = ["pending", "due_now", "completed"]

    # Validate payment status
    if payment.payee_payment_status not in valid_payment_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid payment status. Allowed values are 'pending', 'due_now', 'completed'.",
        )

    payment_id_obj = convert_str_to_objectid(payment_id)

    # Fetch the existing payment
    existing_payment = await payments_collection.find_one({"_id": payment_id_obj})
    if not existing_payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Check evidence_id requirement based on the existing payment
    existing_evidence_id = existing_payment.get("evidence_id")
    if existing_evidence_id:
        # If evidence_id exists, ensure the new payment instance includes it
        if not payment.evidence_id:
            raise HTTPException(
                status_code=400,
                detail="Evidence ID is required as it already exists in the payment.",
            )
        # Validate the provided evidence_id
        evidence_id_obj = convert_str_to_objectid(payment.evidence_id)
        evidence = await files_collection.find_one({"_id": evidence_id_obj})
        if not evidence:
            raise HTTPException(
                status_code=404, detail="Evidence file not found for the given ID"
            )
    else:
        # If evidence_id does not exist, allow updating without it
        payment.evidence_id = None

    # Update the payment
    payment.payee_due_date = convert_date_to_datetime(payment.payee_due_date)
    result = await payments_collection.update_one(
        {"_id": payment_id_obj}, {"$set": payment.dict()}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Payment not found")

    return {"status": "success"}

# Delete a payment and its associated evidence
@router.delete("/payments/{payment_id}")
async def delete_payment(payment_id: str):
    payment_id_obj = convert_str_to_objectid(payment_id)
    payment = await payments_collection.find_one({"_id": payment_id_obj})

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Delete associated evidence file
    if payment.get("evidence_id"):
        evidence_id_obj = convert_str_to_objectid(payment["evidence_id"])
        await files_collection.delete_one({"_id": evidence_id_obj})

    result = await payments_collection.delete_one({"_id": payment_id_obj})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Payment not found")

    return {"status": "success"}
