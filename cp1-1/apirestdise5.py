from flask import Flask, request, jsonify
import json
app = Flask(__name__)
tareas_file = 'tareasAPI_RESTFul.json'
# Ruta para obtener todas las tareas (GET)
@app.route('/tareas', methods=['GET'])
def obtener_todas_las_tareas():
    tareas = cargar_tareas()
    tareas_con_enlaces = []
    for tarea in tareas:
        tarea_con_enlace = tarea.copy()
        tarea_con_enlace['enlace'] = f"/tareas/{tarea['id']}"
        tareas_con_enlaces.append(tarea_con_enlace)
    return jsonify({"tareas": tareas_con_enlaces})
# Ruta para crear una nueva tarea (POST)
@app.route('/tareas', methods=['POST'])
def crear_tarea():
    nueva_tarea = request.json.get('tarea')
    if nueva_tarea:
        tareas = cargar_tareas()
        nuevo_id = max(tareas, key=lambda x:x['id'])['id'] + 1 if tareas else 1
        tarea = {
            'id': nuevo_id,
            'tarea': nueva_tarea }
        tareas.append(tarea)
        guardar_tareas(tareas)
        return jsonify({"mensaje": "Tarea creada correctamente", "id": nuevo_id, "enlace": f"/tareas/{nuevo_id}"}), 201
    else:
        return jsonify({"mensaje": "Falta el parámetro 'tarea'"}), 400
# Ruta para obtener una tarea específica (GET)
@app.route('/tareas/<int:id>', methods=['GET'])
def obtener_tarea(id):
    tareas = cargar_tareas()
    tarea = next((t for t in tareas if t['id'] == id), None)
    if tarea:
        tarea_con_enlace = tarea.copy()
        tarea_con_enlace['enlace'] = f"/tareas/{id}"
        return jsonify(tarea_con_enlace)
    else:
        return jsonify({"mensaje": "El ID de tarea no existe"}), 404
# Función para cargar tareas desde el archivo
def cargar_tareas():
    try:
        with open(tareas_file, 'r') as file:
            tareas = json.load(file)
        return tareas
    except FileNotFoundError:
        return []
# Función para guardar tareas en el archivo
def guardar_tareas(tareas):
    with open(tareas_file, 'w') as file:
        json.dump(tareas, file)
if __name__ == '__main__':
    app.run(debug=True)
