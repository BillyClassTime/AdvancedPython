# test/unit_integration.py

import unittest
import os
from fastapi.testclient import TestClient
from main import app

class TestSecurityRoutes(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_login(self):
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")
        response = self.client.post(f"/token?username={username}&password={password}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())

class TestRabbitMQRoutes(unittest.TestCase):
    token = None
    
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")
        response = cls.client.post(f"/token?username={username}&password={password}")   
        cls.token  = response.json()["access_token"]
            
    def setUp(self):
        self.client = TestClient(app)

    def test_publish_consume_message_flow(self):
        if self.__class__.token is None:
            self.skipTest("Se requiere un token válido para esta prueba.")
        # Test publishing a message
        mensaje = "TestMessage"
        response_publish = self.client.post(f"/publicar/{mensaje}", headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response_publish.status_code, 200)
        self.assertIn("mensaje", response_publish.json())

        # Test consuming the published message
        response_consume = self.client.get("/consumir", headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response_consume.status_code, 200)
        self.assertIn("mensajes", response_consume.json())
        self.assertIn("TestMessage", response_consume.json()["mensajes"])

if __name__ == "__main__":
    unittest.main() 