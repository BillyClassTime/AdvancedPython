import unittest
import ejercicio1Grupo1TodDo as ejercicio1respuesta
import json

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = ejercicio1respuesta.app.test_client()
        self.app.testing = True

        # Crear una tarea para las pruebas
        result = self.app.post('/tasks', 
                               data=json.dumps({'description': 'Test task', 'completed': False}), 
                               content_type='application/json')
        print(result.data)
        self.task_id = json.loads(result.data)['task_id']

    def tearDown(self):
        # Eliminar la tarea después de la prueba
        self.app.delete(f'/tasks/{self.task_id}')

    def test_get_tasks(self):
        print("Prueba de recuperación de tareas (GET)...")
        result = self.app.get('/tasks')
        self.assertEqual(result.status_code, 200, "Se esperaba un código de estado 200")
        print("Prueba de recuperación de tareas (GET) completada con éxito.")

    def test_create_task(self):
        print("Prueba de creación de tarea (POST)...")
        result = self.app.post('/tasks', data=json.dumps({'description': 'Test task', 'completed': False}), content_type='application/json')
        self.assertEqual(result.status_code, 201, "Se esperaba un código de estado 201")
        task_id = json.loads(result.data)['task_id']
        print("Prueba de creación de tarea (POST) completada con éxito.")

        print("Eliminando la tarea creada...")
        delete_result = self.app.delete(f'/tasks/{task_id}')
        self.assertEqual(delete_result.status_code, 200, "Se esperaba un código de estado 200 al eliminar la tarea")
        print("Tarea eliminada con éxito.")
        
    def test_update_task(self):
        print("Prueba de actualización de tarea (PUT)...")
        result = self.app.put(f'/tasks/{self.task_id}', data=json.dumps({'description': 'Updated task', 'completed': True}), content_type='application/json')
        self.assertEqual(result.status_code, 200, "Se esperaba un código de estado 200")
        print("Prueba de actualización de tarea (PUT) completada con éxito.")

    def test_delete_task(self):
        print("Prueba de eliminación de tarea (DELETE)...")
        result = self.app.delete(f'/tasks/{self.task_id}')
        self.assertEqual(result.status_code, 200, "Se esperaba un código de estado 200")
        print("Prueba de eliminación de tarea (DELETE) completada con éxito.")

    def test_read_nonexistent_task(self):
        print("Prueba de recuperación de tarea inexistente (GET)...")
        result = self.app.get('/tasks/999')  # Cambia el ID a uno que no exista
        self.assertEqual(result.status_code, 404, "Se esperaba un código de estado 404 para una tarea inexistente")
        print("Prueba de recuperación de tarea inexistente (GET) completada con éxito.")

    def test_update_nonexistent_task(self):
        print("Prueba de actualización de tarea inexistente (PUT)...")
        result = self.app.put('/tasks/999', data=json.dumps({'description': 'Updated task', 'completed': True}), content_type='application/json')
        self.assertEqual(result.status_code, 404, "Se esperaba un código de estado 404 para una tarea inexistente")
        print("Prueba de actualización de tarea inexistente (PUT) completada con éxito.")

    def test_delete_nonexistent_task(self):
        print("Prueba de eliminación de tarea inexistente (DELETE)...")
        result = self.app.delete('/tasks/999')  # Cambia el ID a uno que no exista
        self.assertEqual(result.status_code, 404, "Se esperaba un código de estado 404 para una tarea inexistente")
        print("Prueba de eliminación de tarea inexistente (DELETE) completada con éxito.")

if __name__ == '__main__':
    unittest.main()