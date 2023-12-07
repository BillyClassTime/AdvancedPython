import asynctest
from fastapi.testclient import TestClient
import unittest
import os

from services.rabbitMQServices import RabbitMQ
from app_core.utils.messagetobase64 import conform_message_response
from main import app
class TestRabbitMQIntegration(asynctest.TestCase):
    id_request = None

    @classmethod
    def setUpClass(cls):
        #Obtener token
        cls.id_request  = None # "e37d2ec8-b4d0-401d-9b0b-97750bc48c33" #id de la solicitud

    async def test_a_connectMQ(self):
        try:
            self.rabbitmq = RabbitMQ()
            await self.rabbitmq.connect()
            await self.rabbitmq.close()
            self.assertTrue(True)
        except Exception as e:
            self.assertTrue(False)

    async def test_b_publish_message_request(self):
        try:
            self.rabbitmq = RabbitMQ()
            await self.rabbitmq.connect()
            test_message = {
                "nombre": "Juan",
                "edad": 30,
                "ciudad": "Madrid"
            }
            #id_request = await self.rabbitmq.publish_message(test_message)
            id_request = await self.rabbitmq.publish_message_request(test_message)
            if id_request is not None and len(id_request) > 0:
                self.__class__.id_request = id_request
            print(f"Id de la solicitud: {id_request}")
            await self.rabbitmq.close()
            self.assertTrue(True)
        except Exception as e:
            self.assertTrue(False)

    async def test_c_publish_message_response(self):
        if self.__class__.id_request is None:
            self.skipTest("No se ha podido obtener el id de la solicitud")
        try:
            self.rabbitmq = RabbitMQ()
            await self.rabbitmq.connect()
            test_message = {
                "analisis_mensaje": "Nombre: Juan, Edad: 30, Ciudad: Madrid",
                "fecha_análisis": "2021-05-01 12:00:00",
                "analista": "Analista 1",
                "resultado": "Nombres de personas: 1, Nombres de ciudades: 1, Edades: 1"
            }
            await self.rabbitmq.publish_message_response(self.id_request,test_message)
            await self.rabbitmq.close()
            self.assertTrue(True)
        except Exception as e:
            self.assertTrue(False)            


    async def test_d_consume_messages_request(self):
        if self.__class__.id_request is None:
            self.skipTest("No se ha podido obtener el id de la solicitud")
        try:
            self.rabbitmq = RabbitMQ()
            await self.rabbitmq.connect()
            async def callback(message):
                if message.body is not None and len(message.body) > 0:
                    #print(f"Test_d_Mensaje de solicitud: {message.body.decode('utf-8')}")
                    self.assertTrue(True)
                else:
                    test_message = {}
                    self.assertEqual(message,test_message) 
            await self.rabbitmq.consume_message_request(self.id_request,callback)
            await self.rabbitmq.close()
            self.assertTrue(True)            
        except Exception as e:
            self.assertTrue(False)

    async def test_e_consume_messages_response(self):
        if self.__class__.id_request is None:
            self.skipTest("No se ha podido obtener el id de la solicitud")
        try:
            self.rabbitmq = RabbitMQ()
            await self.rabbitmq.connect()
            async def callback(message):
                if message.body is not None and len(message.body) > 0:
                    self.assertTrue(True)
                    #print(f"Mensaje de respuesta: {message.body.decode('utf-8')}")
                else:
                    test_message = {}
                    self.assertEqual(message,test_message) 
            await self.rabbitmq.consume_message_response(self.id_request,callback)
            await self.rabbitmq.close()
            self.assertTrue(True)
        except Exception as e:
            self.assertTrue(False)        

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
    id_request = None
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")
        response = cls.client.post(f"/token?username={username}&password={password}")   
        cls.token  = response.json()["access_token"]
        cls.id_request = None # "c6dd778a-0aea-4736-85d6-f29a6608abca" #id de la solicitud
            
    def setUp(self):
        self.client = TestClient(app)

    def test_a_publish_message_request(self):
        if self.__class__.token is None:
            self.skipTest("Se requiere un token válido para esta prueba.")
        # Test publishing a message requesst
        test_message = {
                "nombre": "Juan",
                "edad": 30,
                "ciudad": "Madrid"
            }
        response_publish = self.client.post(f"/publicar_mensaje_solicitud",
                                            json=test_message,
                                            headers={"Authorization": f"Bearer {self.token}"})
        #print(f"\nJSON de Respuesta de publica_mensaje_solicitud:{response_publish.json()}")
        self.assertEqual(response_publish.status_code, 200)
        self.assertIn("id_solicitud", response_publish.json())
        self.__class__.id_request = response_publish.json()["id_solicitud"]
        #print(f"Id de la solicitud: {self.__class__.id_request}")

    def test_b_publish_message_response(self):
        if self.__class__.token is None:
            self.skipTest("Se requiere un token válido para esta prueba.")
        if self.__class__.id_request is None:
            self.skipTest("Se requiere un id de solicitud válido para esta prueba.")
        # Test publishing a message response
        test_message = {
            "analisis_mensaje": "Nombre: Juan, Edad: 30, Ciudad: Madrid",
            "fecha_análisis": "2021-05-01 12:00:00",
            "analista": "Analista 1",
            "resultado": "Nombres de personas: 1, Nombres de ciudades: 1, Edades: 1"
        }
        id_request = self.__class__.id_request
        response_publish = self.client.post(f"/publicar_mensaje_respuesta/{id_request}",
                                            json=test_message,
                                            headers={"Authorization": f"Bearer {self.token}"})
        #print(response_publish)
        self.assertEqual(response_publish.status_code, 200)
        self.assertIn("id_solicitud", response_publish.json())
        #print(response_publish.json())
        self.assertEqual(response_publish.json()["id_solicitud"], id_request)
    
    def test_c_consume_message_request(self):
        if self.__class__.token is None:
            self.skipTest("Se requiere un token válido para esta prueba.")
        if self.__class__.id_request is None:
            self.skipTest("Se requiere un id de solicitud válido para esta prueba.")
        # Test consuming the message of the request
        id_request = self.__class__.id_request
        response_consume = self.client.get(f"/consumir_mensaje_solicitud/{id_request}", 
                                           headers={"Authorization": f"Bearer {self.token}"})
        #print(f"Response: {response_consume}")   
        #print(f"Response JSON: {response_consume.json()}")

        #self.assertEqual(response_consume.status_code, 200)
        #self.assertIn("request_analisis", response_consume.json()["kind"])

    def test_d_consume_message_response(self):
        if self.__class__.token is None:
            self.skipTest("Se requiere un token válido para esta prueba.")
        if self.__class__.id_request is None:
            self.skipTest("Se requiere un id de solicitud válido para esta prueba.")
        # Test consuming the message of the response
        id_request = self.__class__.id_request
        response_consume = self.client.get(f"/consumir_mensaje_respuesta/{id_request}", 
                                           headers={"Authorization": f"Bearer {self.token}"})
        response_json = response_consume.json()
        if 'estado' in response_json:
            self.assertEqual(response_json, {'estado': 'error', 'detalle': 'no se recibio ningun mensaje'})
        else:
            self.assertEqual("response_analisis", response_json["kind"])

if __name__ == '__main__':
    asynctest.main()
    unittest.main()        