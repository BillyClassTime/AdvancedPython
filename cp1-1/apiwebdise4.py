from flask import Flask, request, jsonify
app = Flask(__name__)
tareas = []
# Ruta para obtener todas las tareas
@app.route('/tareas', methods=['GET'])
def obtener_tareas():
    try:
        if not tareas:
            raise Exception("No hay tareas disponibles.")
        return jsonify({"tareas": tareas}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404
# Ruta para crear una nueva tarea
@app.route('/tareas', methods=['POST'])
def crear_tarea():
    try:
        nueva_tarea = request.json.get('tarea')
        if not nueva_tarea:
            raise Exception("Falta el parámetro 'tarea'.")
        tareas.append(nueva_tarea)
        return jsonify({"mensaje": "Tarea creada correctamente"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
if __name__ == '__main__':
    app.run(debug=True)
