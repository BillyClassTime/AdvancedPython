from flask import Flask, request
from flask_jwt_extended import (JWTManager, create_access_token, 
                                jwt_required, get_jwt_identity)
app = Flask(__name__)
# Clave secreta para firmar tokens JWT
app.config['JWT_SECRET_KEY'] = 'my-secret-key'  
jwt = JWTManager(app)
# Ruta de inicio de sesión que emite un token JWT al usuario
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    if username == 'usuario' and password == 'contraseña':
        access_token = create_access_token(identity=username)
        return {'access_token': access_token}, 200
    return {'mensaje': 'Credenciales incorrectas'}, 401
# Ruta segura que requiere autenticación mediante un token JWT
@app.route('/recurso-seguro', methods=['GET'])
@jwt_required()
def recurso_seguro():
    current_user = get_jwt_identity()
    return {'mensaje': f'Acceso concedido a {current_user}'}

if __name__ == '__main__':
    app.run(debug=True)
