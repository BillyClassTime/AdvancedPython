from flask import Flask, request, jsonify
import json
app = Flask(__name__)
tareas_file = 'tareas.json'
# Ruta para obtener todas las tareas
@app.route('/tareas', methods=['GET'])
def obtener_todas_las_tareas():
    try:
        with open(tareas_file, 'r') as file:
            tareas = json.load(file)
        return jsonify({"tareas": tareas})
    except FileNotFoundError:
        return jsonify({"tareas": []})
# Ruta para crear una nueva tarea
@app.route('/tareas', methods=['POST'])
def crear_tarea():
    nueva_tarea = request.json.get('tarea')
    if nueva_tarea:
        try:
            with open(tareas_file, 'r') as file:
                tareas = json.load(file)
        except FileNotFoundError:
            tareas = []
        tareas.append(nueva_tarea)
        with open(tareas_file, 'w') as file:
            json.dump(tareas, file)
        return jsonify({"mensaje": "Tarea creada correctamente"}), 201
    else:
        return jsonify({"mensaje": "Falta el parámetro 'tarea'"}), 400
if __name__ == '__main__':
    app.run(debug=True)
