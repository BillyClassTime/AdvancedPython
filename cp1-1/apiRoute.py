from flask import Flask, jsonify, abort 
app = Flask(__name__)
products = []
users = []
# Punto 1: Rutas con direccion URL especifica
# Rutas de productos y usuarios 
# Punto 2: Jerarquia lógica - Organizamos la jerarquia de las rutas
# Punto 3: Nombres descriptivos
# Punto 4: Métodos apropiados para cada ruta (GET, POST, PUT, DELETE) ApiWeb
@app.route('/api/v1.0/products', methods=['GET'])
def get_products():
    return jsonify({'products': products})

@app.route('/api/v1.0/products/<int:product_id>', methods=['GET'])
def get_productbyId(product_id):
    product = [product for product in products if product['id'] == product_id]
    if len(product) == 0:
        abort(404)
    return jsonify({'product': product[0]})

@app.route('/api/v1.0/users', methods=['GET'])
def get_users():
    return jsonify({'users': users})

@app.route('/api/v1.0/users/<int:user_id>', methods=['GET'])
def get_userbyId(user_id):
    user = [user for user in users if user['id'] == user_id]
    if len(user) == 0:
        abort(404)
    return jsonify({'user': user[0]})

# Punto 5: Definir Rutas anidadas si las hay (Optional)
@app.route('/api/v1.0/users/<int:user_id>/products', methods=['GET'])
def get_user_products(user_id):
    user = [user for user in users if user['id'] == user_id]
    if len(user) == 0:
        abort(404)
    return jsonify({'products': user[0]['products']})

# Punto 6: Gestión de errores
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    # Punto 7: Ejecutar el servidor
    app.run(debug=True)