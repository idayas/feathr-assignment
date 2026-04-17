from pymongo import MongoClient, ReturnDocument
from bson import json_util
import json

client = MongoClient('mongo', 27017, username='root', password='example')
db = client.feathr
conn = db.products

def get_next_product_id():
    counter = db.counters.find_one_and_update(
        {"_id": "productId"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return f"P{counter['seq']:04d}"

def format_json(data):
    return json.loads(json_util.dumps(data))

def get_all_products():
    return format_json(conn.find())


def create_product(name=None, category=None, price=None, quantity=None):
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


    if not quantity and price != 0:
        errors.append("Missing required field: quantity (number)")
    else:
        try:
            quantity = int(quantity)
        except ValueError:
            errors.append("quantity must be an integer")

    if errors:
        return format_json({"status": "error", "error": "Missing required fields", "messages": errors})

    conn.insert_one({
        "ProductId": get_next_product_id(),
        "ProductName": name,
        "ProductCategory": category,
        "Price": price,
        "AvailableQuantity": quantity
    })
    return format_json({"status": "success", "data": conn.find_one(sort=[("_id", -1)])})


def get_product(product_id):
    if product_id is None:
        return format_json({"status": "error", "messages": ["Missing required field: product_id (string)"]})

    if not conn.find_one({"ProductId": product_id}):
        return format_json({"status": "error", "messages": ["Product not found"]})
    
    return format_json({"status": "success", "data": conn.find_one({"ProductId": product_id})})

def update_product(product_id=None, name=None, category=None, price=None, quantity=None):
    updates = {}
    if product_id is None:
        return format_json({"status": "error", "messages": ["Missing required field: product_id (string)"]})

    if name is not None:
        updates["ProductName"] = name

    if category is not None:
        updates["ProductCategory"] = category

    if price is not None:
        try:
            updates["Price"] = float(price)
        except (ValueError, TypeError):
            return format_json({"status": "error", "messages": ["price must be a number"]})

    if quantity is not None:
        try:
            updates["AvailableQuantity"] = int(quantity)
        except (ValueError, TypeError):
            return format_json({"status": "error", "messages": ["quantity must be an integer"]})

    if not updates:
        return format_json({"status": "error", "messages": ["No fields to update"]})

    conn.update_one({"ProductId": product_id}, {"$set": updates})
    return format_json({"status": "success", "data": conn.find_one({"ProductId": product_id})})


def delete_product(product_id=None):
    if product_id is None:
        return format_json({"status": "error", "messages": ["Missing required field: product_id (string)"]})

    result = conn.delete_one({"ProductId": product_id})
    if result.deleted_count == 0:
        return format_json({"status": "error", "messages": ["Product not found"]})

    return format_json({"status": "success"})

def seed_data():
    conn.insert_many([
        {
            "ProductId": get_next_product_id(),
            "ProductName": "Product 1",
            "ProductCategory": "Category 1",
            "Price": 10.99,
            "AvailableQuantity": 100
        },
        {
            "ProductId": get_next_product_id(),
            "ProductName": "Product 2",
            "ProductCategory": "Category 2",
            "Price": 19.99,
            "AvailableQuantity": 50
        },
        {
            "ProductId": get_next_product_id(),
            "ProductName": "Product 3",
            "ProductCategory": "Category 3",
            "Price": 5.99,
            "AvailableQuantity": 200
        }
    ])

    return format_json({"status": "success", "data": conn.find()})
