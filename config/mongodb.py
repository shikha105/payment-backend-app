
#from pymongo.mongo_client import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://shikha105789:5CaaH9hZdgFnHs5H@payment-app-cluster.4045c.mongodb.net/?retryWrites=true&w=majority&appName=payment-app-cluster"

# Create a new client and connect to the server
client = AsyncIOMotorClient(uri, server_api = ServerApi('1'))


db = client.payapp_db
payments_collection = db["payments"]
files_collection = db["files"]

