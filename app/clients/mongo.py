from pymongo import MongoClient
import os

db_name = os.getenv("MONGO_DATABASE", "feathr")

client = MongoClient(
    host=os.getenv("MONGO_HOST", "mongo"),
    port=int(os.getenv("MONGO_PORT", "27017")),
    username=os.getenv("MONGO_USERNAME", "root"),
    password=os.getenv("MONGO_PASSWORD", "example"),
)

db = client[db_name]
