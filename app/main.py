from flask import Flask, request
from init_es import init_elasticsearch
import product_service

app = Flask(__name__)

init_elasticsearch()

@app.route('/products', methods=['GET', 'POST', 'DELETE'])
def products():
    if request.method == 'GET':
        return product_service.get_all_products()
    elif request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get( 'category' )
        price = request.form.get( 'price' )
        quantity = request.form.get( 'quantity' )
        description = request.form.get( 'description' )
        return product_service.create_product(name, category, price, quantity, description)
    elif request.method == 'DELETE':
        return product_service.delete_all_products()


@app.route('/product/<string:product_id>', methods=['GET', 'PUT', 'DELETE'])
def product(product_id):
    if request.method == 'GET':
        return product_service.get_product(product_id)
    elif request.method == 'PUT':
        name = request.form.get('name')
        category = request.form.get( 'category' )
        price = request.form.get( 'price' )
        quantity = request.form.get( 'quantity' )
        description = request.form.get( 'description' )
        return product_service.update_product(product_id, name, category, price, quantity, description)
    elif request.method == 'DELETE':
        return product_service.delete_product(product_id)

@app.route('/products/search', methods=['GET'])
def search():
    query = request.args.get('query')
    return product_service.search_products(query)

@app.route('/products/analytics', methods=['GET'])
def analytics():
    return product_service.get_analytics()

@app.route('/seed', methods=['GET'])
def seed():
    return product_service.seed_data()

if __name__ == '__main__': 
    app.run(host='0.0.0.0', port='5070', debug = True) 
    
