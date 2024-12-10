
from fastapi import APIRouter, UploadFile, HTTPException
from config.mongodb import files_collection, payments_collection
from utils import convert_str_to_objectid
from io import BytesIO
from fastapi.responses import StreamingResponse
from datetime import datetime

router = APIRouter()

@router.post("/payments/{payment_id}/upload_evidence/")
async def upload_evidence(payment_id: str, file: UploadFile):
    payment_id_obj = convert_str_to_objectid(payment_id)

    if not file.content_type in ["application/pdf", "image/png", "image/jpeg"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    payment = await payments_collection.find_one({"_id": payment_id_obj})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Prepare file data
    file_data = {
        "payment_id": payment_id_obj,
        "filename": file.filename,
        "content": await file.read(),
        "updated_on": datetime.utcnow()
    }

    # Insert file data into files_collection
    result = await files_collection.insert_one(file_data)

    # Link evidence to the payment
    await payments_collection.update_one(
        {"_id": payment_id_obj},
        {"$set": {"evidence_id": str(result.inserted_id)}}
    )

    return {"status": "file uploaded", "evidence_id": str(result.inserted_id)}

@router.get("/payments/{payment_id}/download_evidence/")
async def download_evidence(payment_id: str):
    payment_id_obj = convert_str_to_objectid(payment_id)

    # Get payment document to find evidence_id
    payment = await payments_collection.find_one({"_id": payment_id_obj})
    if not payment or "evidence_id" not in payment:
        raise HTTPException(status_code=404, detail="No evidence linked to this payment")

    evidence_id_obj = convert_str_to_objectid(payment["evidence_id"])

    # Fetch evidence from files_collection
    file = await files_collection.find_one({"_id": evidence_id_obj})
    if not file:
        raise HTTPException(status_code=404, detail="Evidence file not found")

    # Prepare file content as a stream for downloading
    file_content = BytesIO(file["content"])

    return StreamingResponse(
        file_content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={file['filename']}"}
    )

@router.get("/files/{file_id}")
async def get_evidence_by_id(file_id: str):
    file_id_obj = convert_str_to_objectid(file_id)

    # Fetch evidence by file_id
    file = await files_collection.find_one({"_id": file_id_obj})
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    return {
        "status": "success",
        "file_data": {
            "file_id": str(file["_id"]),
            "payment_id": str(file["payment_id"]),
            "filename": file["filename"],
            "updated_on": file["updated_on"].isoformat() if "updated_on" in file else None,
        }
    }
