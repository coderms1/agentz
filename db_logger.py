import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv


load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["swarmhq"]
logs = db["logs"]

def log_query(agent_name, question, response):
    logs.insert_one({
        "agent": agent_name,
        "question": question,
        "response": response,
        "timestamp": datetime.utcnow()
    })
