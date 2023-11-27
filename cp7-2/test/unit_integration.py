import unittest
import asynctest
import os
from fastapi.testclient import TestClient

from services.rabbitMQServices import RabbitMQ
from app_core.initializer import app

class TestRabbitMQIntegration(asynctest.TestCase):
    async def test_publish_messageMQ(self):
        try:
            self.rabbitmq = RabbitMQ()
            await self.rabbitmq.connect()
            test_message = "test message"
            await self.rabbitmq.publish_message(test_message)
            await self.rabbitmq.close()
            self.assertTrue(True)
        except Exception as e:
            self.assertTrue(False)

    async def test_consume_messagesMQ(self):
        try:
            self.rabbitmq = RabbitMQ()
            await self.rabbitmq.connect()
            async def callback(message):
                if message is not None and len(message) > 0:
                    self.assertTrue(True)
                else:
                    test_message = []
                    self.assertEqual(message,test_message)       
            await self.rabbitmq.consume_messages(callback)
            await self.rabbitmq.close()
            self.assertTrue(True)
        except Exception as e:
            self.assertTrue(False)


class TestRoutes(unittest.TestCase):
    token = None #Token Valido para las pruebas

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        #Obtener token
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")
        response = cls.client.post(f"/token?username={username}&password={password}")   
        cls.token  = response.json()["access_token"]

    def setUp(self):
        self.client = TestClient(app)

    def test_login(self):
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")
        response = self.client.post(f"/token?username={username}&password={password}")
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json()["access_token"])

    def test_publicar_mensajeAPI(self):
        if self.__class__.token is None:
            self.skipTest("Se requiere un token válido para esta prueba.")
        mensaje = "test message"
        response = self.client.post(f"/publicar/{mensaje}", 
                                    headers={"Authorization": f"Bearer {self.token}"})        
        self.assertEqual(response.status_code, 200)

    def test_publicar_mensaje_sin_autenticacionAPI(self):
        mensaje = "test message"
        try:
            response = self.client.post(f"/publicar/{mensaje}")        
            self.assertEqual(response.status_code, 401)
        except Exception as e:
            self.assertTrue(True)

    def test_consumir_mensajeAPI(self):
        if self.__class__.token is None:
            self.skipTest("Se requiere un token válido para esta prueba.")
        response = self.client.get("/consumir", 
                                    headers={"Authorization": f"Bearer {self.token}"})        
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json()["mensajes"])

    # Agregar más pruebas según sea necesario

if __name__ == '__main__':
    asynctest.main()
    unittest.main()