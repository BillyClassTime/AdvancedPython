from flask import Flask, request, jsonify
app = Flask(__name__)
usuarios = []
# Ruta para obtener un usuario por su ID (poco coherente)
@app.route('/obtener_usuario/<int:id>', methods=['GET'])
def obtener_usuario_por_id(id):
    #for usuario in usuarios:
    #    if usuario['id'] == id:
    #        return jsonify(usuario)
    users_with_id = [usuario for usuario in usuarios if usuario['id'] == id]
    if users_with_id:
        return jsonify(users_with_id)        
    return jsonify({"mensaje": "Usuario no encontrado"})
# Ruta para obtener todos los usuarios (coherente)
@app.route('/usuarios', methods=['GET'])
def obtener_todos_los_usuarios():
    return jsonify({"usuarios": usuarios})
# Ruta para crear un nuevo usuario (poco coherente)
@app.route('/agregar', methods=['POST'])
def agregar_usuario():
    nuevo_usuario = request.json
    usuarios.append(nuevo_usuario)
    return jsonify({"mensaje": "Usuario agregado correctamente"})
if __name__ == '__main__':
    app.run(debug=True)
