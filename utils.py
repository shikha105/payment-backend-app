
from datetime import datetime, date
from bson import ObjectId

def convert_date_to_datetime(payment_date: date) -> datetime:
    """Converts a datetime.date object to datetime.datetime at midnight."""
    if isinstance(payment_date, date):
        return datetime.combine(payment_date, datetime.min.time())
    return payment_date


def convert_to_date(date_value):
    """
    Converts a date string to a datetime.date object.
    If the date is already a datetime.date object, it returns it as is.
    """
    if isinstance(date_value, str):
        return datetime.fromisoformat(date_value).date()
    elif isinstance(date_value, datetime):
        return date_value.date()
    return date_value  # Return as is if already a date object

    

def convert_objectid_to_str(doc):
    """Converts all ObjectId fields in a dictionary to string."""
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)
        elif isinstance(value, dict):
            convert_objectid_to_str(value)  # Recursive for nested dictionaries
    return doc

def convert_str_to_objectid(payment_id: str) -> ObjectId:
    """Convert a string to ObjectId, raise HTTPException if invalid."""
    try:
        return ObjectId(payment_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payment_id format")