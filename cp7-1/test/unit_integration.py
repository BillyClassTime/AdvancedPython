import unittest
from fastapi.testclient import TestClient
from app_core.initializer import app

class TestManageRoutes(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_redirect_to_docs(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
       # self.assertEqual(response.headers["location"], "/docs")

    def test_publicar_mensaje(self):
        mensaje = "Hola, esto es un mensaje de prueba"
        response = self.client.post(f"/publicar/{mensaje}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mensaje": f"Mensaje '{mensaje}' publicado correctamente en la cola."})

    def test_publicar_mensaje_negativo(self):
       # Prueba negativa: mensaje vacío
        mensaje_negativo = ""
        response_negativo = self.client.post(f"/publicar/{mensaje_negativo}")
        self.assertEqual(response_negativo.status_code, 404)  # El código 404 es para datos no procesables en FastAPI

    def test_consumir(self):
        # Confirmar que hay mensajes en la cola para una respuesta positiva
        self.client.post("/publicar/mensaje_de_prueba")
        response = self.client.get("/consumir")
        self.assertEqual(response.status_code, 200)  # Código 200 para una respuesta positiva

    def test_consumir_sin_mensajes(self): # Prueba negativa: no hay mensajes en la cola
        response = self.client.get("/consumir")
        self.assertEqual(response.status_code, 404)  # No hay mensajes en la cola en las pruebas

    # Agregar más pruebas según sea necesario

if __name__ == "__main__":
    unittest.main()   