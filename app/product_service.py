from clients import db, es, es_index
from pymongo import ReturnDocument
from bson import json_util
import json
import random

conn = db.products

def get_next_product_id():
    counter = db.counters.find_one_and_update(
        {"_id": "productId"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return f"P{counter['seq']:04d}"

def strip_id(product):
    if not product:
        return product

    product = dict(product)
    product.pop("_id", None)
    return product


def format_json(data):
    return json.loads(json_util.dumps(data))

def get_all_products():
    products = conn.find()

    cleaned = []
    for product in products:
        cleaned.append(strip_id(product))

    return format_json({"status": "success", "data": cleaned})


def create_product(name=None, category=None, price=None, quantity=None, description=None):
    errors = []
    if not name:
        errors.append("Missing required field: name (string)")

    if not category:
        errors.append("Missing required field: category (string)")

    if not description:
        errors.append("Missing required field: description (string)")

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

    doc = {
        "ProductId": get_next_product_id(),
        "ProductName": name,
        "ProductCategory": category,
        "Price": price,
        "AvailableQuantity": quantity,
        "ProductDescription": description
    }

    conn.insert_one(doc)
    
    # Get the latest product
    cleaned = strip_id(conn.find_one(sort=[("_id", -1)]))

    es.index(index=es_index, id=doc["ProductId"], document=doc)
    return format_json({"status": "success", "data": cleaned})


def get_product(product_id):
    if product_id is None:
        return format_json({"status": "error", "messages": ["Missing required field: product_id (string)"]})

    product = conn.find_one_and_update(
        {"ProductId": product_id},
        {"$inc": {"ViewCount": 1}},
        return_document=ReturnDocument.AFTER
    )

    if not product:
        return format_json({"status": "error", "messages": ["Product not found"]})

    cleaned = strip_id(product)
    
    return format_json({"status": "success", "data": cleaned})

def update_product(product_id=None, name=None, category=None, price=None, quantity=None, description=None):
    updates = {}
    if product_id is None:
        return format_json({"status": "error", "messages": ["Missing required field: product_id (string)"]})

    if name is not None:
        updates["ProductName"] = name

    if category is not None:
        updates["ProductCategory"] = category


    if category is not None:
        updates["ProductDescription"] = description 

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

    es.update(index=es_index, id=product_id, doc=updates)

    cleaned = strip_id(conn.find_one({"ProductId": product_id}))

    return format_json({"status": "success", "data": cleaned})


def delete_product(product_id=None):
    if product_id is None:
        return format_json({"status": "error", "messages": ["Missing required field: product_id (string)"]})

    result = conn.delete_one({"ProductId": product_id})
    if result.deleted_count == 0:
        return format_json({"status": "error", "messages": ["Product not found"]})

    es.delete(index=es_index, id=product_id)

    return format_json({"status": "success"})


def delete_all_products(): 
    # NOTE: This would not be ideal in production, this is just to make it eaiser for testing
    result = conn.delete_many({})

    db.counters.update_one({"_id": "productId"}, {"$set": {"seq": 0}})

    es.delete_by_query(index=es_index, query={"match_all": {}})

    return format_json({"status": "success", "messages": ["Deleted all products"]})

def search_products(query=None):
    if not query:
        return format_json({"status": "error", "messages": ["Missing required field: query (string)"]})

    query = query.replace(",", " ")

    res = es.search(index=es_index, query={
        "match": { "ProductDescription": {"query": query, "operator": "and"}}
    })

    products = []
    product_ids = []

    for hit in res["hits"]["hits"]:
        p = hit["_source"]
        products.append(p)
        product_ids.append(p["ProductId"])

    if product_ids:
        conn.update_many({"ProductId": {"$in": product_ids}}, {"$inc": {"SearchCount": 1}})

    return format_json({"status": "success", "data": products})

def get_analytics():
    total_products = conn.count_documents({})

    avg_price_per_product_results = list(conn.aggregate([
       {"$group": {"_id": None, "avg_price": {"$avg": "$Price"}}}
    ]))

    avg_price_per_cat_results = list(conn.aggregate([
       {"$group": {"_id": "$ProductCategory", "avg_price": {"$avg": "$Price"}}}
    ]))

    total_in_category = list(conn.aggregate([
       {"$group": {"_id": "$ProductCategory", "count": {"$sum": 1}}},
       {"$sort": {"count": -1}}
    ]))

    most_searched = list(conn.aggregate([
       {"$sort": {"SearchCount": -1}},
       {"$limit": 5}
    ]))

    most_viewed = list(conn.aggregate([
       {"$sort": {"ViewCount": -1}},
       {"$limit": 5}
    ]))

    most_searched = [strip_id(p) for p in most_searched]
    most_viewed = [strip_id(p) for p in most_viewed]

    avg_price_per_product = avg_price_per_product_results[0]["avg_price"] if avg_price_per_product_results else 0
    avg_price_per_cat = avg_price_per_cat_results[0]["avg_price"] if avg_price_per_cat_results else 0

    total_in_cat = {}
    for t in total_in_category:
        total_in_cat[t["_id"]] = int(t["count"])

    return format_json({
        "status": "success",
        "data": {
            "most_searched": most_searched,
            "most_viewed": most_viewed,
            "total_products": total_products,
            "avg_price_per_product": float(f'{avg_price_per_product:.2f}'), 
            "avg_price_per_cat": float(f'{avg_price_per_cat:.2f}'),
            "total_in_category": total_in_cat 
        }
    })

def seed_data():
    categories = ["Electronics", "Clothing", "Food"]
    adjectives = ["Premium", "Basic", "Smart", "Classic", "Fresh", "Deluxe"]
    items = ["Mouse", "Keyboard", "Jacket", "Shoes", "Juice", "Snack"]

    products = []

    for _ in range(10):
        name = f"{random.choice(adjectives)} {random.choice(items)}"
        category = random.choice(categories)
        price = random.randint(5, 100) + 0.99
        quantity = random.randint(1, 200)

        products.append({
            "ProductId": get_next_product_id(),
            "ProductName": name,
            "ProductCategory": category,
            "Price": price,
            "AvailableQuantity": quantity,
            "ProductDescription": f"This item is a {name} in the {category} category",
            "ViewCount": 0,
            "SearchCount": 0
        })

    conn.insert_many(products)

    products = [strip_id(p) for p in products]

    # NOTE: There is probably a better way to do this
    for product in products:

        # Mongo mutates the original product object and adds an _id, so we make a copy and remove it
        # to prevent it from erroring when sending to elastic

        es_doc = dict(product) 
        es_doc.pop("ViewCount", None)
        es_doc.pop("SearchCount", None)
        es.index(index="products", id=product["ProductId"], document=es_doc)

    return format_json({"status": "success", "data": products})
