from flask import Flask, request, jsonify
app = Flask(__name__)
tareas = []
# Ruta para obtener todas las tareas
@app.route('/tareas', methods=['GET'])
def obtener_tareas():
    """
    Obtiene la lista completa de tareas.
    Respuesta:
    - 200 OK: Lista de tareas en formato JSON.
    """
    return jsonify({"tareas": tareas}), 200
# Ruta para crear una nueva tarea
@app.route('/tareas', methods=['POST'])
def crear_tarea():
    """
    Crea una nueva tarea.
    Parámetros:
    - tarea (str): Descripción de la tarea.
    Respuesta:
    - 201 Created: Tarea creada correctamente en formato JSON.
    - 400 Bad Request: Parámetros incorrectos en formato JSON.
    """
    nueva_tarea = request.json.get('tarea')
    if nueva_tarea:
        tareas.append(nueva_tarea)
        return jsonify({"mensaje": "Tarea creada correctamente"}), 201
    return jsonify({"mensaje": "Parámetros incorrectos"}), 400
if __name__ == '__main__':
    app.run(debug=True)
