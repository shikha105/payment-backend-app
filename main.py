
from fastapi import FastAPI

from routes import payments, files
from services.payment_service import normalize_csv_and_insert
app = FastAPI()

#commenting now as once data is inserted in the db 
@app.on_event("startup")
async def load_initial_data():
    csv_path = "./sample_data/payment_information.csv"
    await normalize_csv_and_insert(csv_path) 

# Register routes
app.include_router(payments.router, prefix="/payments", tags=["Payments"])
app.include_router(files.router, prefix="/files", tags=["Files"])

@app.get("/")
def root():
    return {"message": "Payment API is up and running"}
