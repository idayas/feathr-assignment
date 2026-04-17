from flask import Flask, request
import product_service

app = Flask(__name__)

@app.route('/products', methods=['GET', 'POST'])
def products():
    if request.method == 'GET':
        return product_service.get_all_products()
    elif request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get( 'category' )
        price = request.form.get( 'price' )
        quantity = request.form.get( 'quantity' )
        return product_service.create_product(name, category, price, quantity)


@app.route('/product/<string:product_id>', methods=['GET', 'PUT', 'DELETE'])
def product(product_id):
    if request.method == 'GET':
        return product_service.get_product(product_id)
    elif request.method == 'PUT':
        name = request.form.get('name')
        category = request.form.get( 'category' )
        price = request.form.get( 'price' )
        quantity = request.form.get( 'quantity' )
        return product_service.update_product(product_id, name, category, price, quantity)
    elif request.method == 'DELETE':
        return product_service.delete_product(product_id)

@app.route('/seed', methods=['GET'])
def seed():
    return product_service.seed_data()

if __name__ == '__main__': 
    app.run(host='0.0.0.0', port='5070', debug = True) 
    
