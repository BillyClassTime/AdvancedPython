# Importamos libraries
from flask import Flask, jsonify, request
import psycopg2
from psycopg2 import OperationalError

app= Flask(__name__)

# configuración y connexion a la base de datos PostgreSQL
def get_db_connection():
    try:
        conn = psycopg2.connect(database="postgres", 
                            user="postgres",password="your_password", 
                            host="localhost", port="5432")
        return conn
    except OperationalError as e:
        print(e)
        return None

# Revisar ruta y endpoints
#GET /tasks` (Recupera la lista de todas las tareas)
@app.route('/tasks', methods=['GET'])
def get_tasks():
    conn = get_db_connection() 
    if conn is None:
        return jsonify({'Error':'Con la base de datos'}), 500
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM tasks")
        rows = cur.fetchall()
        conn.close()
        return jsonify(rows)
    except OperationalError as e:
        return handle_db_request(e)

#POST /tasks` (Crea una nueva tarea)
@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    conn = get_db_connection()
    if conn is None:
        return jsonify({'Error':'Con la base de datos'}), 500
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO tasks (description,completed) VALUES (%s, %s) returning task_id",
                (data['description'],data.get('completed',False))) 
        task_id = cur.fetchone()[0]
        conn.commit()
        conn.close()
        #return jsonify({'message': 'New task created!'})
        return jsonify({'task_id': task_id}), 201
    except OperationalError as e:
        return handle_db_request(e)

#GET /tasks/<task_id>` (Recupera una tarea específica)
@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_taks_byid(task_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({'Error':'Con la base de datos'}), 500
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM tasks WHERE task_id = {task_id}")
        rows = cur.fetchall()
        conn.close()
        if not rows:
            return jsonify({'message': 'Task not found!'}),404
        return jsonify(rows)
    except OperationalError as e:
        return handle_db_request(e)

#PUT /tasks/<task_id>` (Actualiza una tarea específica)
@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    if not data or not 'description' in data or 'completed ' in data:
        return jsonify({'message': 'invalid values!'}),400
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({'Error':'Con la base de datos'}), 500
    try:
        cur = conn.cursor()
        cur.execute("UPDATE tasks SET description = %s, completed = %s WHERE task_id = %s", 
                    (data['description'], data['completed'],f"{task_id}"))
        if cur.rowcount == 0:
            return jsonify({'message': 'Task not found!'}),404
        conn.commit()
        conn.close()
        return jsonify({'message': 'Task updated!'})
    except OperationalError as e:
        return handle_db_request(e)

#DELETE /tasks/<task_id>` (Elimina una tarea específica)
@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({'Error':'Con la base de datos'}), 500
    try:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM tasks WHERE task_id ={task_id}")
        if cur.rowcount == 0:
            return jsonify({'message': 'Task not found!'}),404
        conn.commit()
        conn.close()
        return jsonify({'message': 'Task deleted!'})
    except OperationalError as e:
        return handle_db_request(e) 

# Manejo de errores con la base de datos
@app.errorhandler(OperationalError)
def handle_db_request(e):
    return jsonify({'Error':'Con la base de datos','message':str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
