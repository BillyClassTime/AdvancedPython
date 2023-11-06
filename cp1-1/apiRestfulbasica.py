from flask import Flask, jsonify
app = Flask(__name__)
# Recurso: elementos
# Punto 1: Rutas con direccion URL especifica
# Rutas de productos y usuarios 
# Punto 2: Jerarquia lógica - Organizamos la jerarquia de las rutas
# Punto 3: Nombres descriptivos
# Punto 4: Métodos apropiados para cada ruta (GET, POST, PUT, DELETE) ApiWeb
# Ruta para obtener todos los elementos
@app.route('/api/v1.0/elements', methods=['GET'])
def get_elements():
    try:
        elements = ["element1", "element2", "element3"]
        return jsonify({'elements': elements}),200
    except:
        return jsonify({'error': elements}),500
# Ruta para obtener un elemento por su id
@app.route('/api/v1.0/elements/<int:element_id>', methods=['GET'])
def get_elementbyId(element_id):
    try:
        elements = ["element1", "element2", "element3"]
        if element_id >= len(elements):
            return jsonify({'error': 'Not found'}), 404
        else:
            element = elements[element_id]
            return jsonify({'element': element}),200
    except:
        return jsonify({'error': elements}),500
# Punto 5: Gestion de errores
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'Internal Server Error'}), 500

# Punto 6: Ejecutar el servidor
if __name__ == '__main__':
    app.run(debug=True)