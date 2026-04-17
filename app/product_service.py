from pymongo import MongoClient
from bson import json_util, ObjectId
import json

client = MongoClient('mongo', 27017, username='root', password='example')
db = client.feathr
conn = db.products

def format_json(data):
    return json.loads(json_util.dumps(data))

def get_all_products():
    return format_json(conn.find())


def create_product(name=None, category=None, price=None):
    errors = []
    if not name:
        errors.append("Missing required field: name (string)")

    if not category:
        errors.append("Missing required field: category (string)")

    if not price and price != 0:
        errors.append("Missing required field: price (number)")
    else:
        try:
            price = float(price)
        except ValueError:
            errors.append("price must be a number")

    if errors:
        return format_json({"status": "error", "error": "Missing required fields", "messages": errors})

    conn.insert_one({"name": name, "category": category, "price": price})
    return format_json({"status": "success", "data": conn.find_one(sort=[("_id", -1)])})


def get_product(product_id):
    return format_json({"status": "success", "data": conn.find_one({"_id": ObjectId(product_id)})})

def update_product(product_id, name=None, category=None, price=None):
    updates = {}
    if name is not None:
        updates["name"] = name

    if category is not None:
        updates["category"] = category

    if price is not None:
        try:
            updates["price"] = float(price)
        except (ValueError, TypeError):
            return format_json({"status": "error", "messages": ["price must be a number"]})

    if not updates:
        return format_json({"status": "error", "messages": ["No fields to update"]})

    conn.update_one({"_id": ObjectId(product_id)}, {"$set": updates})
    return format_json({"status": "success", "data": conn.find_one({"_id": ObjectId(product_id)})})


def delete_product(product_id):
    result = conn.delete_one({"_id": ObjectId(product_id)})
    if result.deleted_count == 0:
        return format_json({"status": "error", "messages": ["Product not found"]})

    return format_json({"status": "success"})

def seed_data():
    conn.insert_many([
        {
            "name": "Product 1",
            "category": "Category 1",
            "price": 10.99
        },
        {
            "name": "Product 2",
            "category": "Category 2",
            "price": 19.99
        },
        {
            "name": "Product 3",
            "category": "Category 3",
            "price": 29.99
        }
    ])

    return format_json({"status": "success", "data": conn.find()})
