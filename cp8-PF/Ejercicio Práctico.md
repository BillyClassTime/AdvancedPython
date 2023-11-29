# Ejercicio Práctico

## Integración patrones de diseño con Python FastAPI y Colas en RabbitMQ

### Escenario

Una compañía tiene un servicio de análisis de datos, donde sus clientes acceden por intermedio de un servicio `front-end` con su usuario y contraseña, y envian con un `json` los datos a analisar.

Estos datos son recogidos por varios analistas, quienes recogen los datos en otro servicio `front-end`  y tras realizar el análisis, envían los resultados.

Los clientes que han enviado a analiza sus datos, recogen el resultado en el mismo servicio `front-end`. Terminando el proceso.

En este ejercicicio práctico construiresmos el `middleware`y analizaremos el patrón **  `cola de mensajes` ** 

Este complejo escenario incluiremos automatización de pruebas con Postman en entornos multicapa con enfoque en arquitecturas de microservicios.

### 1. Entorno de midleware apirestful

1. Crear la estructura de su proyecto

   ```powershell
   My Proyect:
   ├───api
   │   └───routes
   │       └─── __init__.py
   │       └─── rabbitMQRoutes.py
   │       └─── securityRoutes.py
   ├───app_core
   │   └───utils
   │       └──__init_.py
   │       └──messagetobase64.py
   │   └─── __init__.py
   │   └─── initializer.py
   ├───custom_exceptions
   │   └─── __init__.py
   │   └─── customExceptions
   │   └─── rabbitMQExceptions.py
   ├───services
   │   └─── __init__.py
   │   └─── rabbitMQServices.py
   │   └─── securityServices.py
   ├───env
   │       #Python 3.9.10
   └───test
   │   └───__init__.py
   │       unit_integration.py
   .env
   main.py
   requeriment.txt
   ```
   
   - Crear el entorno para python y activarlo
   
      ```powershell
      py -3.9 -m venv env
      ```
   
      Actualizar e Instalar las librerias para el proyecto
   
      ```powershell
      py -m pip install --upgrade pip
      pip install fastapi uvicorn aio_pika python-dotenv httpx pyjwt asynctest


   - Crear las variables del entorno en su fichero .env
     
     ```python
     RABBITMQ_USERNAME=usuario
     RABBITMQ_PASSWORD=clave
     RABBITMQ_HOST=url a rabbitMQ
     RABBITMQ_VHOST=\
     RABBITMQ_PORT=5672
     SECRET_KEY = "mikeysecreta"
     ALGORITHM = "HS256"
     ACCESS_TOKEN_EXPIRE_MINUTES = 30
     API_USERNAME=usuario api
     API_PASSWORD=clave del usuario api
     ```

2. Crear los servicios
   - Los servicios que gestionarán la seguridad OAuth2 y JWT

     ```python
     import jwt
     from jwt import InvalidTokenError
     from datetime import datetime, timedelta
     from typing import Optional
     from fastapi import Depends
     from fastapi.security import OAuth2PasswordBearer
     from dotenv import load_dotenv
     import os
     from custom_exceptions.customExceptions import customException
     
     # Cargar la configuración de secret key y algoritmo para JWT
     load_dotenv()
     class SecurityConfig:
         SECRET_KEY = os.getenv("SECRET_KEY")
         ALGORITHM = os.getenv("ALGORITHM")
         ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
     
     config = SecurityConfig()
     
     # Configurar OAuth2
     oatuh2_scheme = OAuth2PasswordBearer(tokenUrl="token")
     
     # Función para generar un Token JWT
     def create_jwt_token(data: dict, expires_delta: Optional[timedelta] = None):
         to_encode = data.copy()
         if expires_delta:
             expire = datetime.utcnow() + expires_delta
         else:
             expire = datetime.utcnow() + timedelta(minutes=15)
         to_encode.update({"exp": expire})
         encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
         return encoded_jwt
     
     # Función para obtener el token desde la solicitud HTTP
     def get_current_user(token: str = Depends(oatuh2_scheme)):
         try:
             payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
             username: str = payload.get("sub")
             if username is None:
                 raise customException("No se encontró el nombre de usuario")
         except jwt.ExpiredSignatureError:# 4. Manejar el caso en que el token ha expirado
             raise customException("El token ha expirado")
         except InvalidTokenError:             # 5. Manejar el caso en que el token no es válido        
             raise customException("El token no es válido")
         except Exception as e:
             raise customException("Error desconocido")
         return username
     ```
     
   - Los servicios que gestionaran la interacción con `RabbitMQ`

     ```python
     import os
     import aio_pika
     from custom_exceptions.rabbitMQExceptions import RabbitMQError
     from app_core.utils.messagetobase64 import conform_message_request, conform_message_response
     from dotenv import load_dotenv
     import json
     
     load_dotenv() # Carga las variables de entorno del fichero .env	
     
     class RabbitMQ:
         def __init__(self):
             rabbitmq_host = os.getenv("RABBITMQ_HOST")
             rabbitmq_port = os.getenv("RABBITMQ_PORT")
             rabbitmq_user = os.getenv("RABBITMQ_USERNAME")
             rabbitmq_password = os.getenv("RABBITMQ_PASSWORD")
             rabbitmq_vhost = os.getenv("RABBITMQ_VHOST").replace("\\","") if os.getenv("RABBITMQ_VHOST") else None
             self.connection_string = f'amqp://{rabbitmq_user}:{rabbitmq_password}@{rabbitmq_host}:{rabbitmq_port}/{rabbitmq_vhost}'
             #self.connection_string = 'amqp://usuario:clave@hostvhost'
             self.exchange_name = 'analysis_exchange'
             self.connection = None
         
         async def connect(self):
             try:
                 self.connection = await aio_pika.connect_robust(self.connection_string)
             except aio_pika.exceptions.AMQPError as e:
                 raise RabbitMQError(f"Error al conectar con RabbitMQ: {str(e)}")
         
         async def __create_channel(self):
             return await self.connection.channel()
     
         async def __declare_queue(self, channel, queue_name):
             return await channel.declare_queue(queue_name, durable=True)
     
         async def __publish_message(self, channel, exchange, routing_key, message):
             await exchange.publish(
                 aio_pika.Message(json.dumps(message).encode(),
                                  delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                                  expiration=360000),
                 routing_key=routing_key, timeout=30
             )
                     
         async def publish_message_request(self, mensaje):
             if not self.connection:
                 await self.__connect()
             try:
                 message_request = conform_message_request(mensaje)
                 id_request = message_request['id']
                 queue_name = f"queue_{id_request}_request"
                 routing_key_name = f"routing_key_{id_request}_request"
     
                 channel = await self.__create_channel()
                 exchange = await channel.declare_exchange(self.exchange_name, aio_pika.ExchangeType.DIRECT, durable=True)
                 queue = await self.__declare_queue(channel, queue_name)
                 await queue.bind(exchange, routing_key=routing_key_name)
                 await self.__publish_message(channel, exchange, routing_key_name, message_request)
             
             except aio_pika.exceptions.AMQPError as e:
                 errorMensaje="Error al publicar mensaje de request en RabbitMQ"
                 print(f"{errorMensaje}: {e}")
                 raise RabbitMQError(f"{errorMensaje}: {e}")
             return id_request
                 
         async def publish_message_response(self, id_request, message):
             if not self.connection:
                 await self.__connect()
             try:
                 response_message = conform_message_response(id_request, message)                            
                 queue_name = f"queue_{id_request}_response"
                 routing_key_name = f"routing_key_{id_request}_response"
                             
                 channel = await self.__create_channel()
                 exchange = await channel.declare_exchange(self.exchange_name, aio_pika.ExchangeType.DIRECT, durable=True)
                 queue = await self.__declare_queue(channel, queue_name)
                 await queue.bind(exchange, routing_key=routing_key_name)
                 await self.__publish_message(channel, exchange, routing_key_name, response_message)
         
             except aio_pika.exceptions.AMQPError as e:
                 errorMensaje="Error al publicar mensaje de response en RabbitMQ"
                 print(f"{errorMensaje}: {e}")
                 raise RabbitMQError(f"{errorMensaje}: {e}")
             return id_request          
     
         async def consume_message_response(self, id_request, callback):
             if not self.connection:
                 await self.__connect()
             try:
                 queue_name = f"queue_{id_request}_response"
                 routing_key_name = f"routing_key_{id_request}_response"
                 channel = await self.__create_channel()
                 exchange = await channel.declare_exchange(self.exchange_name, aio_pika.ExchangeType.DIRECT, durable=True)
                 queue = await self.__declare_queue(channel, queue_name)
                 await queue.bind(exchange, routing_key=routing_key_name)
                 await queue.consume(callback, no_ack=True)
             except aio_pika.exceptions.AMQPError as e:
                 errorMensaje="Error al consumir mensaje de response en RabbitMQ"
                 print(f"{errorMensaje}: {e}")
                 raise RabbitMQError(f"{errorMensaje}: {e}")    
     
         async def consume_message_request(self, id_request,callback):
             if not self.connection:
                 await self.__connect()
             try:
                 queue_name = f"queue_{id_request}_request"
                 routing_key_name = f"routing_key_{id_request}_request"
                 channel = await self.__create_channel()
                 exchange = await channel.declare_exchange(self.exchange_name, aio_pika.ExchangeType.DIRECT, durable=True)
                 queue = await self.__declare_queue(channel, queue_name)
                 await queue.bind(exchange, routing_key=routing_key_name)
                 await queue.consume(callback, no_ack=True)
             except aio_pika.exceptions.AMQPError as e:
                 errorMensaje="Error al consumir mensaje de request en RabbitMQ"
                 print(f"{errorMensaje}: {e}")
                 raise RabbitMQError(f"{errorMensaje}: {e}")
                         
         async def close(self):
             if self.connection:
                 await self.connection.close()                
     ```

3. Crear Excepciones personalizadas

   - Las excepciones personalizadas para gestión de errores de seguridad 

     ``` python
     from fastapi import HTTPException, status
     
     class customException(HTTPException):
         def __init__(self, detail: str):
             super().__init__(
                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                 detail=detail
             )
     ```

   - Las excepciones personalizadas para gestión de errores con el RabbitMQ

     ```python
     class RabbitMQError(Exception):
         def __init__(self, mensaje):
             super().__init__(mensaje)
     ```

4. Implementar las utilidades propias del proyecto

   - Manipulación de mensajes para envío de solicitudes y resultado de análisis

     ```python
     import json
     import base64
     import uuid
     
     def messageToBase64(message):
         data_str = json.dumps(message)
         encoded_data = base64.b64encode(data_str.encode("utf-8")).decode("utf-8")
         return encoded_data
     
     def base64ToMessage(encoded_message):
         decoded_data = base64.b64decode(encoded_message).decode("utf-8")
         message = json.loads(decoded_data)
         return message
     
     def conform_message_request(message):
         request_message = {
             "id": "",
             "kind": "request_analisis",
             "mensaje": message
         }
         mensaje_id = str(uuid.uuid4())
         request_message['id'] = mensaje_id
         encoded_message = messageToBase64(message)
         request_message['mensaje'] = encoded_message
         return request_message
     
     def conform_message_response(id, message):
         response_message = {
             "id": "",
             "kind": "response_analisis",
             "mensaje": message
         }
         response_message['id'] = id
         encoded_message = messageToBase64(message)
         response_message['mensaje'] = encoded_message
         return response_message
     
     if __name__ == "__main__":
         message = {
             "nombre": "Juan",
             "edad": 30,
             "ciudad": "Madrid"
         }
         request_message = conform_message_request(message)
         message = {
             "analisis_mensaje": "Nombre: Juan, Edad: 30, Ciudad: Madrid",
             "fecha_análisis": "2021-05-01 12:00:00",
             "analista": "Analista 1",
             "resultado": "Nombres de personas: 1, Nombres de ciudades: 1, Edades: 1"
         }
         response_message = conform_message_response(request_message['id'], message)
         print(f"JSON de solicitud: {request_message}")
         print(f"JSON de respuesta: {response_message}")
     
     ```

     

5. Gestionar las rutas de su APIRest

   - Ruta para gestión de seguridad

     ```python
     from datetime import timedelta
     from fastapi import APIRouter
     from services.securityServices import create_jwt_token,config
     
     router = APIRouter()
     
     @router.post("/token")
     def login(username: str, password: str):
         # Aquí deberías realizar la autenticación del usuario y verificar las credenciales
         # Por simplicidad, este ejemplo asume que el usuario y la contraseña son correctos
         expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
         access_token = create_jwt_token(data={"sub": username}, expires_delta=expires)
         return {"access_token": access_token, "token_type": "bearer"}
     ```

   - Ruta para interación con RabbitMQ

     ```python
     import asyncio
     from fastapi import APIRouter, Depends, HTTPException
     from fastapi.responses import RedirectResponse
     import json
     
     from services.rabbitMQServices import RabbitMQ
     from services.securityServices import get_current_user
     
     route = APIRouter() 
     
     from fastapi import Body
     
     @route.post("/publicar_mensaje_solicitud", response_model=dict, tags=["RabbitMQ"] ,summary="Publicar mensaje de solicitud")
     async def publicar_mensaje_solicitud(mensaje: dict = Body(...), current_user: str=Depends(get_current_user)):
         rabbitmq = None
         try:
             if current_user is None:
                 raise HTTPException(status_code=401, detail=f"usuario:{current_user}, no autorizado")
             rabbitmq = RabbitMQ()
             await rabbitmq.connect()
             id_request = await rabbitmq.publish_message_request(mensaje)
             return {f"id_solicitud": id_request,"estado": "publicado"}
         except Exception as e:
             print(f"Excepción publicando el mensaje:{e}")
             return {"id_solicitud": None, "estado": f"error:{e}"}
         finally:
             if rabbitmq is not None:
                 await rabbitmq.close()
     
     @route.get("/consumir_mensaje_solicitud/{id_request}", response_model=dict, tags=["RabbitMQ"] ,summary="Consumir mensaje de solicitud")
     async def consumir_mensaje_solicitud(id_request: str, str=Depends(get_current_user)):
         mensaje_solicitud_future = asyncio.Future()
         rabbitmq = None
         try:
             rabbitmq = RabbitMQ()
             await rabbitmq.connect()
     
             async def callback(mensaje):
                 if mensaje is not None and mensaje.body is not None and len(mensaje.body) > 0:
                     print(f"Recibidos mensajes: {mensaje.body}")
                     mensaje_solicitud_future.set_result(mensaje.body.decode("utf-8"))
                 else:
                     mensaje_solicitud_future.set_result("{}")
     
             await rabbitmq.consume_message_request(id_request,callback)
             mensaje_solicitud = await asyncio.wait_for(mensaje_solicitud_future, timeout=5) #espera 5 segundos
             if mensaje_solicitud is None:
                 return {"estado": "error","detalle" :"no se recibio ningun mensaje"}
             try:
                 return json.loads(mensaje_solicitud)
             except json.JSONDecodeError as jde:
                 print(f"Excepción decodificando el mensaje: {jde}")
                 return {"estado": f"error:{jde}"}
             
         except HTTPException as he:
             print(f"Excepcion HTTP consumiendo el mensaje: {he.detail}")
             return {"estado": f"error:{he.detail}"}
         except asyncio.TimeoutError as te:
             print(f"Excepcion Timeout consumiendo el mensaje: {te}")
             return {"estado": f"error:{te}"}
         finally:
             if rabbitmq is not None:
                 await rabbitmq.close()
     
     @route.post("/publicar_mensaje_respuesta/{id_request}", response_model=dict, tags=["RabbitMQ"] ,summary="Publicar mensaje de respuesta")
     async def publicar_mensaje_respuesta(id_request:str,mensaje: dict = Body(...), current_user: str=Depends(get_current_user)):
         rabbitmq = None
         try:
             #print(f"Publicando mensaje: {mensaje}")
             if current_user is None:
                 raise HTTPException(status_code=401, detail=f"usuario:{current_user}, no autorizado")
             #else:
             #    print(f"Usuario autenticado: {current_user}")
             rabbitmq = RabbitMQ()
             await rabbitmq.connect()
             id_request_respuesta = await rabbitmq.publish_message_response(id_request,mensaje)
             return {"id_solicitud": id_request,"estado": "publicado"}
         except Exception as e:
             print(f"Excepción publicando el mensaje:{e}")
             return {"id_solicitud": None, "estado": f"error:{e}"}
         finally:
             if rabbitmq is not None:
                 await rabbitmq.close()
     
     @route.get("/consumir_mensaje_respuesta/{id_request}", response_model=dict, tags=["RabbitMQ"] ,summary="Consumir mensaje de solicitud")
     async def consumir_mensaje_respuesta(id_request: str, str=Depends(get_current_user)):
         mensaje_respuesta_future = asyncio.Future()
         rabbitmq = None
         try:
             rabbitmq = RabbitMQ()
             await rabbitmq.connect()
     
             async def callback(mensaje):
                 if mensaje is not None and mensaje.body is not None and len(mensaje.body) > 0:
                     print(f"Recibidos mensajes: {mensaje.body}")
                     mensaje_respuesta_future.set_result(mensaje.body.decode("utf-8"))
                 else:
                     mensaje_respuesta_future.set_result("{}")
     
             await rabbitmq.consume_message_response(id_request,callback)
             mensaje_respuesta = await asyncio.wait_for(mensaje_respuesta_future, timeout=5) #espera 5 segundos
             if mensaje_respuesta is None:
                 return {"estado": "error","detalle" :"no se recibio ningun mensaje"}
             try:
                 return json.loads(mensaje_respuesta)
             except json.JSONDecodeError as jde:
                 print(f"Excepción decodificando el mensaje: {jde}")
                 return {"estado": f"error:{jde}"}
             
         except HTTPException as he:
             print(f"Excepcion HTTP consumiendo el mensaje: {he.detail}")
             return {"estado": f"error:{he.detail}"}
         except asyncio.TimeoutError as te:
             print(f"Excepcion Timeout consumiendo el mensaje: {te}")
             return {"estado": f"error:{te}"}
         finally:
             if rabbitmq is not None:
                 await rabbitmq.close()
        
     
     
     @route.get("/", response_class=RedirectResponse, status_code=302,include_in_schema=False)
     async def redirect_to_docs():
         return "/docs"        
     ```

6. Implementar el Inicializador

   - Cree el punto de conexión entre la entrada inicial y los demás componentes del proyecto

     ```python
     from api.routes import rabbitMQRoutes
     from api.routes import securityRoutes
     from fastapi import FastAPI, HTTPException
     from custom_exceptions.customExceptions import customException
     from fastapi.middleware.cors import CORSMiddleware
     import logging
     
     app = FastAPI()
     
     logging.basicConfig(filename='logs.log', level=logging.DEBUG, 
                         format='%(asctime)s %(levelname)s %(name)s %(message)s')
     logger = logging.getLogger(__name__)
     
     @app.exception_handler(HTTPException)
     async def exception_handler(request, exc: HTTPException):
         logger.error(f"{exc.detail}")
         error_message = f"{exc.detail}"
         raise HTTPException(status_code=500,detail=error_message)
     
     @app.exception_handler(customException)
     async def exception_handler(request, exc: customException):
         logger.error(f"{exc.detail}")
         error_message = f"{exc.detail}"
         raise HTTPException(status_code=500,detail=error_message)
     
     origins = [
         "http://localhost:8000",
         "http://127.0.0.1:8000"]
     
     app.add_middleware(
         CORSMiddleware,
         allow_origins=origins,
         allow_credentials=True,
         allow_methods=["GET","POST","PUT","DELETE"],
         allow_headers=["*"],
     )
     
     app.include_router(rabbitMQRoutes.route)
     app.include_router(securityRoutes.router)
     ```
   
7. Implemente el fichero principal del proyecto

   - Implemente el punto inicial

     ```python
     from app_core.initializer import app
     
     if __name__ == "__main__":
         import uvicorn
         uvicorn.run(app, host="127.0.0.1", port=20000)
     ```


7. Pruebe la aplicación en Open API

   - Este proyecto tiene una redirección desde la ruta raiz `\` a `\docs`, inicie su navegador y ponga: `http:\\localhost:15000` 

     ![01](img/01.png)
     
     Recuerde que RabbitMQ debe estar en ejecución, y su url deberá estar en: `RABBITMQ_HOST=url a rabbitMQ`, confirme que su servidor esta accesible antes de continuar con las pruebas.
     
     > **Nota:** Si puede publicar y consumir mensajes, siga adelante

8. Pruebas unitarias

   - Preparar el estado inicial con comandos de `RabbitMQ`
   
     Estos comandos están activos en la versión `3.12.7` para otras versiones pueden seguir disponible, sin embargo consulte la referencia de la versión para mayor exactitud.
     
     Nota: para ver la version actual puede usar: `rabbitmqctl status`
     
     | Descripción                            | comando                                                      |
     | -------------------------------------- | ------------------------------------------------------------ |
     | Listar todas las colas                 | rabbitmqadmin list queues                                    |
     | Ver el tamaño de una cola              | rabbitmqadmin get queue=name_de_la_cola                      |
     | Listar los mensajes de una cola        | rabbitmqadmin get queue=name_de_la_cola count=N*             |
     | Purgar una cola                        | rabbitmqadmin purge queue name=name_de_la_cola               |
     | Listar Exchanges                       | rabbitmqadmin list exchanges                                 |
     | Listar Vínculos de un Exchange         | rabbitmqadmin list bindings=nombre_del_exchange              |
     | Listar Vínculos de una cola especifica | rabbitmqadmin list bindings destination_type=queue destination=nombre_de_la_cola |
     | Borrar una cola                        | rabbitmqadmin delete queue name=nombre_de_la_cola            |
     | Borrar un Exchange                     | rabbitmqadmin delete exchange name=nombre_del_exchange       |
     
     `*N` mostrará los N mensajes desde el último hasta el primero.
     
     Cada comando debe ser utilizado con el usuario y contraseña de acceso a rabbit asi:
     
     `rabbitmqadmin -u usuario -p contraseña <comando>`
     
     ejemplo:
     
     `rabbitmqadmin -u usuario -p pasword list queues`
     
     > **Nota**: Si utiliza `docker` en un contenedor docker puede adjuntar la sesion del contenedor desde su linea de comandos así: `docker exec -it my-rabbit /bin/bash`, donde `my-rabbit` es el nombre de su contenedor `docker` en ejecución.
     
     > **Nota:** Antes de iniciar sus pruebas recuerde que es una buena idea comenzar con un `Estado Inicial` donde todo este a cero desde un comienzo, considere utilizar los comandos anteriores para purgar las colas que vayan a participar en sus pruebas.
     
     En ocasiones requerimos combinar la potencia de los comandos de la linea de comandos propia del sistema operativo donde se aloja RabbitMQ. Escenarios donde requerimos borrar muchas colas, con criterios de sin mensajes, que en este escenario son colas que ya han participado del proceso de análisis.
     
     **Borrar todas las colas:**
     
     ```bash
     rabbitmqadmin -u usuario -p clave -f tsv -q list queues name | while read queue; do rabbitmqadmin -u usuario -p clave -q delete queue name=$queue; done
     ```
     
     **Borrar las colas sin mensajes:**
     
     ```bash
     rabbitmqadmin -u usuario -p clave list queues name messages -f tsv | awk '$2 == 0 {print $1}' | xargs -I {} rabbitmqadmin -u usuario -p clave delete queue name={}
     ```
   
   
   - Crear los casos de pruebas con éxito y con error
   
     tendremos tres grupos de casos de uso para comprar toda la lógica posible de nuestra ApiRest
   
     Pruebas de integración con los servicios de gestión de RabbitMQ:
   
     ```python
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
     ```
   
     Pruebas unitarias y de integración con las rutas de seguridad
   
     ```python
     class TestSecurityRoutes(unittest.TestCase):
         def setUp(self):
             self.client = TestClient(app)
     
         def test_login(self):
             username = os.getenv("USERNAME")
             password = os.getenv("PASSWORD")
             response = self.client.post(f"/token?username={username}&password={password}")
             self.assertEqual(response.status_code, 200)
             self.assertIn("access_token", response.json())
     ```
   
     Pruebas unitarias con las rutas de RabbitMQ
   
     ```python
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
     ```
   
     
   
   - Ejecutar las pruebas por cada grupo de casos de uso
   
     Ejecución de las pruebas de integración con las rutas de seguridad
     
     ```powershell
     py -m unittest test.unit_integration.TestSecurityRoutes -v
     test_login (test.unit_integration.TestSecurityRoutes) ... ok
     
     ----------------------------------------------------------------------
     Ran 1 test in 0.014s
     
     OK
     ```
     
     
     
     Ejecución de pruebas de integración con los servicios de RabbitMQ
     
     ```powershell
     py -m unittest test.unit_integration.TestRabbitMQIntegration -v
     test_a_connectMQ (test.unit_integration.TestRabbitMQIntegration) ... ok
     test_b_publish_message_request (test.unit_integration.TestRabbitMQIntegration) ... Id de la solicitud: 5f488cba-128e-4e4f-8afc-5cefd6901b7b
     ok
     test_c_publish_message_response (test.unit_integration.TestRabbitMQIntegration) ... ok
     test_d_consume_messages_request (test.unit_integration.TestRabbitMQIntegration) ... ok
     test_e_consume_messages_response (test.unit_integration.TestRabbitMQIntegration) ... ok
     
     ----------------------------------------------------------------------
     Ran 5 tests in 0.431s
     
     OK
     ```
     
     Ejecución de pruebas de integración con las rutas de RabbitMQ
     
     ```powershell
     py -m unittest test.unit_integration.TestRabbitMQRoutes -v
     test_a_publish_message_request (test.unit_integration.TestRabbitMQRoutes) ... ok
     test_b_publish_message_response (test.unit_integration.TestRabbitMQRoutes) ... ok
     test_c_consume_message_request (test.unit_integration.TestRabbitMQRoutes) ... Recibidos mensajes: b'{"id": "cd7b1560-a6a6-40cc-9d3d-a2caa74fb42d", "kind": "request_analisis", "mensaje": "eyJub21icmUiOiAiSnVhbiIsICJlZGFkIjogMzAsICJjaXVkYWQiOiAiTWFkcmlkIn0="}'
     ok
     test_d_consume_message_response (test.unit_integration.TestRabbitMQRoutes) ... Recibidos mensajes: b'{"id": "cd7b1560-a6a6-40cc-9d3d-a2caa74fb42d", "kind": "response_analisis", "mensaje": "eyJhbmFsaXNpc19tZW5zYWplIjogIk5vbWJyZTogSnVhbiwgRWRhZDogMzAsIENpdWRhZDogTWFkcmlkIiwgImZlY2hhX2FuXHUwMGUxbGlzaXMiOiAiMjAyMS0wNS0wMSAxMjowMDowMCIsICJhbmFsaXN0YSI6ICJBbmFsaXN0YSAxIiwgInJlc3VsdGFkbyI6ICJOb21icmVzIGRlIHBlcnNvbmFzOiAxLCBOb21icmVzIGRlIGNpdWRhZGVzOiAxLCBFZGFkZXM6IDEifQ=="}'
     ok
     
     ----------------------------------------------------------------------
     Ran 4 tests in 0.417s
     
     OK
     ```
     
     Si desea "estresar" las pruebas para ver el comportamiento de las api con varias solicitudes utilice el siguiente script para la prueba de "estres"
     
     ```powershell
     for ($i = 1; $i -le 10; $i++) {
          py -m unittest test.unit_integration.TestRabbitMQRoutes -v
     }
     ```
     
     El resultado adema de ver que en la linea de comandos no haya errores, deberá aparecer en la lista de colas de RabbitMQ, todos los mensajes de solicitud y respuesta procesados:
     
     ```bash
     root@classtime:/# rabbitmqadmin -u usuario -p clave list queues
     +-----------------------------------------------------+----------+
     |                        name                         | messages |
     +-----------------------------------------------------+----------+
     | queue_00a58bbe-c1c7-4aea-8f82-60f724909d55_request  | 0        |
     | queue_00a58bbe-c1c7-4aea-8f82-60f724909d55_response | 0        |
     | queue_218b3266-6437-4254-bd8d-ab66762d8083_request  | 0        |
     | queue_218b3266-6437-4254-bd8d-ab66762d8083_response | 0        |
     | queue_499d7bd7-4032-4437-a0cc-7b70f0cfffcf_request  | 0        |
     | queue_499d7bd7-4032-4437-a0cc-7b70f0cfffcf_response | 0        |
     | queue_5a084e22-236a-450a-9ae8-a969836e6357_request  | 0        |
     | queue_5a084e22-236a-450a-9ae8-a969836e6357_response | 0        |
     | queue_5f488cba-128e-4e4f-8afc-5cefd6901b7b_request  | 0        |
     | queue_5f488cba-128e-4e4f-8afc-5cefd6901b7b_response | 0        |
     | queue_9334ad40-7f46-4729-b986-e6da5e733dd2_request  | 0        |
     | queue_9334ad40-7f46-4729-b986-e6da5e733dd2_response | 0        |
     | queue_a82e3a10-b433-4c98-b796-6ab85d371295_request  | 0        |
     | queue_a82e3a10-b433-4c98-b796-6ab85d371295_response | 0        |
     | queue_b42db1dd-a639-4f22-b66e-9957fc492bad_request  | 0        |
     | queue_b42db1dd-a639-4f22-b66e-9957fc492bad_response | 0        |
     | queue_b89f5299-56b7-48d9-9dca-e2cacc8dd75e_request  | 0        |
     | queue_b89f5299-56b7-48d9-9dca-e2cacc8dd75e_response | 0        |
     | queue_b9b6e779-0877-4433-882c-f63b31f23d3b_request  | 0        |
     | queue_b9b6e779-0877-4433-882c-f63b31f23d3b_response | 0        |
     +-----------------------------------------------------+----------+
     ```
     
     Deberán haber grupos de colas equivalente a la cantidad de interacciones de la prueba de estres por 2 (una para la solicitud, otra para la respuesta)
     
     > **Nota:** Si la pruebas son correctas puede continuar

### 2. Pruebas en Postman para el middleware

1. Crear el entorno

   Cree su entorno para albergar las colecciones

   `Análisis-Desarrollo`

2. Cree las colecciones

   Cree la colección

   ```bash
   AnálisisSolicitudes
   ```
   
3. Crear las variables de entorno

   | Variable | Initial Value          |
   | -------- | ---------------------- |
   | api_url  | http://localhost:20000 |
   | username | su usuario             |
   | password | su contraseña          |
   
4. Crear Solicitudes

   ```
   AnálisisSolicitudes
   ├─── POST Login
   ├─── POST Enviar para análisis
   ├─── GET Rececpción solicitud para análisis
   ├─── POST Envío resultado del análisis
   ├─── GET Recepción Final del resultado del análisis
   ```
   
   - **Logín**
   
     `POST` **login**
   
     **url** `{{api_url}}/token`
   
     ```
     Params:
     username {{username}}
     password {{rabbitmq_password}}
     ```
   
     **Test  y automatización**
   
     ```javascript
     // En el script de tests de la solicitud POST /token
     pm.test("Extraer y almacenar el token", function () {
         // Parsear el cuerpo de la respuesta JSON
         var jsonResponse = pm.response.json();
     
         // Almacenar el token en una variable de entorno
         pm.environment.set("token", jsonResponse.access_token);
     });
     
     pm.test("Obtener token", function () {
       pm.response.to.have.status(200);
     });
     ```
   
   - **Envío para análisis**
   
     `POST` **Envío para análisis**
   
     **url** `{{api_url}}/publicar_mensaje_solicitud`
   
     ```
     Authorization:
     Bearer Token {{token}}
     ```
   
     **Nota:** No ha creado directamente la variable de entorno `token` esta será creada cuando envíe la solicitud de `Login`
   
     **Body** -raw -json
   
     ```json
     {
         "nombre": "Juan",
         "edad": 30,
         "ciudad": "Madrid"
     }
     ```
   
     **Test  y automatización**
   
     ```javascript
     // Analizar el cuerpo JSON de la respuesta
     var responseBody = pm.response.json();
     
     // Extraer el valor de id_solicitud
     var idSolicitud = responseBody.id_solicitud;
     
     // Guardar el valor en la variable de entorno
     pm.environment.set("id_solicitud", idSolicitud);
     
     // Log para verificar
     console.log("ID de solicitud almacenado en la variable de entorno: " + idSolicitud);
     ```
   
      **Nota:** No ha creado una variable de entorno para `id_solicitud` de manera directa, pero la necesitará para comprobar las otras solicitudes de la API Rest.
   
   - **Recepción solicitud para análisis**
   
     `GET` **Recepción solicitud para análisis**
   
     **url** `{{url_api}}/consumir_mensaje_solicitud/{{id_solicitud}}`
   
     ```
     Authorization:
     Bearer Token {{token}}
     ```
   
     **Test y automatización**
   
     ```javascript
     // Obtener el cuerpo JSON de la solicitud
     var responseBody = pm.response.json();
     
     // Decodificar el mensaje de base64 a JSON
     var mensajeBase64 = responseBody.mensaje;
     var mensajeDecodificado = atob(mensajeBase64);
     var mensajeJSON = JSON.parse(mensajeDecodificado);
     
     // Realizar el análisis y conformar el JSON de resultado
     var test_message = {
         "analisis_mensaje": "Nombre: " + mensajeJSON.nombre + ", Edad: " + mensajeJSON.edad + ", Ciudad: " + mensajeJSON.ciudad,
         "fecha_análisis": "2021-05-01 12:00:00",
         "analista": "Analista 1",
         "resultado": "Nombres de personas: 1, Nombres de ciudades: 1, Edades: 1"
     };
     
     // Log para verificar
     console.log("Resultado del análisis:", test_message);
     
     // Guardar el resultado en una variable de entorno (opcional)
     pm.environment.set("resultado_analisis", JSON.stringify(test_message));
     
     // Modificar el cuerpo de la respuesta con el nuevo JSON
     pm.response.json(test_message);
     ```
   
     **Nota:** La automatización de la prueba requerirá que recuperemos de la recepción para análisis el JSON, este vendrá en base64, lo decodificaremos y simularemos una realización de análisis y conformación del mensaje de resultado del análisis.
   
   - **Envío de resultados del análisis**
   
     `POST` **Envío de resultado del análisis**
   
     **url** `{{url_api}}/publicar_mensaje_respuesta/{{id_solicitud}}`
   
     ```json
     Authorization:
     Bearer Token {{token}}
     ```
   
     **Body** -raw -json
   
     ```json
     {{resultado_analisis}}
     ```
   
     **Test y automatización**
   
     ```json
     try {
         // Analizar el cuerpo JSON de la respuesta
         var responseBody = pm.response.json();
     
         // Extraer el valor de id_solicitud de la respuesta si existe
         var idSolicitudEnRespuesta = responseBody && responseBody.id_solicitud;
     
         // Obtener el valor de id_solicitud almacenado en la variable de entorno
         var idSolicitudEnVariable = pm.environment.get("id_solicitud");
     
         // Verificar si ambos valores existen y son iguales
         if (idSolicitudEnRespuesta && idSolicitudEnVariable && idSolicitudEnRespuesta === idSolicitudEnVariable) {
             console.log("La solicitud en la respuesta coincide con la almacenada en la variable de entorno.");
             // Realizar acciones adicionales si la solicitud coincide
         } else {
             console.log("La solicitud en la respuesta NO coincide con la almacenada en la variable de entorno o alguno de los valores es nulo.");
             // Realizar acciones adicionales si la solicitud no coincide o algún valor es nulo
         }
     } catch (error) {
         console.log("Error al procesar la respuesta JSON:", error.message);
         // Manejar el error según sea necesario
     }
     ```
   
     **Nota:** En el proceso de respuesta del análisis, deberán coincidir el id de la solicitud, tanto de envío como de respuesta.
   
   -  **Recepción Final del resultado del análisis**
   
     `GET` **Recepción Final del resultado del análisis**
   
     **url** `{{url_api}}/consumir_mensaje_respuesta/{{id_solicitud}}`
   
     ```
     Authorization:
     Bearer Token {{token}}
     ```
   
     **Test y automatización**
   
     ```json
     // Obtener el cuerpo JSON de la solicitud
     var responseBody = pm.response.json();
     
     // Check if mensaje exists in the response body
     if (responseBody.hasOwnProperty('mensaje')) {
         // Decodificar el mensaje de base64 a JSON
         var mensajeBase64 = responseBody.mensaje;
         var mensajeDecodificado = atob(mensajeBase64);
         var respuestaFinalJSON = JSON.parse(mensajeDecodificado);
     
         // Log para verificar
         console.log("Resultado de la resupuesta final:", respuestaFinalJSON);
     
         // Guardar el resultado en una variable de entorno (opcional)
         pm.environment.set("resultado_final", JSON.stringify(respuestaFinalJSON));
     
         // Modificar el cuerpo de la respuesta con el nuevo JSON
         pm.response.json(respuestaFinalJSON);
     } else {
         console.log('mensaje not found in the response body');
     }
     ```
   
     **Nota:** La recuperación del resultado final del análisis, deberá decodificarse para recuperar el mensaje. Si este es legible y en el estandar de lo esperado, la prueba será válida

### 3. Automatización de solicitudes

1. Cree los script de automatización de pruebas para corroborar cada una de las solicitudes del proyecto. Postman gestiona en una única colección, la gestión directa hacia el servidor `RabbitMQ` y a su `API Rest`

   - **Test** en **Obtener Login** `POST` **login**

     ```javascript
     // En el script de tests de la solicitud POST /token
     pm.test("Extraer y almacenar el token", function () {
         // Parsear el cuerpo de la respuesta JSON
         var jsonResponse = pm.response.json();
     
         // Almacenar el token en una variable de entorno
         pm.environment.set("token", jsonResponse.access_token);
     });
     
     pm.test("Obtener token", function () {
       pm.response.to.have.status(200);
     });
     ```
     
   - **Test** en **Enviar Mensaje** `POST` **Send Message**
   
     ```javascript
     pm.test("Obtener token", function () {
       pm.response.to.have.status(200);
     });
     ```
     
   - **Tests** en **Recibir Mensaje** `GET` **Receive Message**
   
     ```javascript
     pm.test("Obtener token", function () {
       pm.response.to.have.status(200);
     });
     ```
   
   ### 4. Revision de pruebas
   
   - Ejecute las pruebas de la colección
   
     ![02](img/02.png)
   
   - Revise el resultado
   
     ![](img/03.png)
   
   - Revise el resumen detallado
   
     ![](img\04.png)



### 2. Entorno front-end gestion de solicitantes de análisis y analistas 

1. Crear la estructura de su proyecto

   ```powershell
   My Proyect:
   ├─── static
   │    └─── favicon.ico
   ├─── templates
   │   └───index.html
   .env
   main.py
   requeriment.txt
   ```

   - Crear el entorno para python y activarlo

     ```powershell
     py -3.9 -m venv env
     ```

     Actualizar e Instalar las librerias para el proyecto

     ```powershell
     py -m pip install --upgrade pip
     pip install fastapi uvicorn jinja2 httpx pyjwt python-dotenv
     ```


   - cree las variables del entorno en su fichero .env

     ```python
     API_URL=http://<fqdn or ip>:port
     IP_HOST=<ip>
     ```

2. Crear el programa principal

   - Crear script del programa agestor para manipulación de páginas, solicitudes al middleware

     ```python
     import json
     from fastapi import FastAPI, Request, Response,Body
     from fastapi.responses import HTMLResponse, JSONResponse
     from fastapi.staticfiles import StaticFiles
     from fastapi.templating import Jinja2Templates
     import httpx
     import jwt
     import os
     import dotenv   
     
     app = FastAPI()
     
     dotenv.load_dotenv()
     url_base = os.getenv("API_URL")
     
     app.mount("/static", StaticFiles(directory="static"), name="static")
     
     templates = Jinja2Templates(directory="templates")
     
     @app.get("/",response_class=HTMLResponse)
     async def home(request: Request):
         return templates.TemplateResponse("index.html", {"request": request})
     
     @app.post("/login")
     async def login(username: str, password: str, response: Response):
         async with httpx.AsyncClient() as client:
             r = await client.post(f'{url_base}/token', params={'username': username, 'password': password})
         #print(r.json())
         data = r.json()
         token = data['access_token']
         response.set_cookie(key="token", value=token, secure=False)  # Almacena el token en las cookies
         return JSONResponse(content=data)
     
     @app.post("/enviar_para_analisis")
     async def enviar_para_analisis(request: Request, message: str = Body(...)):    
         token = request.headers.get('Authorization')  # Recupera el token de las cabeceras
         if not token:
             return JSONResponse(content={'message': 'No token'})
         headers = {'Authorization': token}
         decoded_token = jwt.decode(token.split(' ')[1], options={"verify_signature": False})
         user = decoded_token['sub']
         message = json.loads(message)
         async with httpx.AsyncClient() as client:
             r = await client.post(f'{url_base}/publicar_mensaje_solicitud',
                                   json={'message': message}, headers=headers)
         if r.content:
             try:
                 data = r.json()
                 print("post del front-end_enviando:",data)
                 id_sol = data.get('id_solicitud')
                 response = JSONResponse(content=data)
                 response.set_cookie(key="id_solicitud", value=str(id_sol), secure=False)  # Almacena el token en las cookies
                 return response
             except:
                 return JSONResponse(content={'message': 'No response body'})
         else:
             return JSONResponse(content={'message': 'No response body'})
     
     @app.get("/recibir_resultado_final_analisis/{id_request}")
     async def recibir_resultado_final_analisis(request: Request, id_request: str):
         token = request.headers.get('Authorization')  # Recupera el token de las cabeceras
         #print(f"recibiendo:{token}")
         if not token:
             return JSONResponse(content={'message': 'No token'})
         headers = {'Authorization': token}
         async with httpx.AsyncClient() as client:
             r = await client.get(f'{url_base}/consumir_mensaje_respuesta/{id_request}', headers=headers)
         if r.content:
             try:
                 data = r.json()
                 print("get del front-end_recibiendo:",data)
                 id_sol = data.get('id_solicitud')
                 if id_request == id_sol:
                     print("son iguales")
                 else:
                     print("son diferentes")
                 return JSONResponse(content=data)
             except:
                 return JSONResponse(content={'message': 'No response body'})
         else:
             return JSONResponse(content={'message': 'No response body'})
         
     @app.get("/recibir_mensaje_para_analisis/{id_request}")  
     async def recibir_mensaje_para_analisis(request: Request, id_request: str):
         token = request.headers.get('Authorization')  
         if not token:
             return JSONResponse(content={'message': 'No token'})
         headers = {'Authorization': token}
         async with httpx.AsyncClient() as client:
             r = await client.get(f'{url_base}/consumir_mensaje_solicitud/{id_request}', headers=headers)
         if r.content:
             try:
                 data = r.json()
                 print("get del front-end_recibiendo_analista:",data)
                 id_sol = data.get('id_solicitud')
                 response = JSONResponse(content=data)
                 return response
             except:
                 return JSONResponse(content={'message': 'No response body'})
         else:
             return JSONResponse(content={'message': 'No response body'})
     
     @app.post("/enviar_resultado_del_analisis")
     async def enviar_resultado_del_analisis(request: Request, message: str = Body(...)):    
         token = request.headers.get('Authorization')
         if not token:
             return JSONResponse(content={'message': 'No token'})
         headers = {'Authorization': token}
         decoded_token = jwt.decode(token.split(' ')[1], options={"verify_signature": False})
         message = json.loads(message)
         id_request = request.cookies.get('id_solicitud')
         async with httpx.AsyncClient() as client:
             r = await client.post(f'{url_base}/publicar_mensaje_respuesta/{id-request}',
                                   json={'message':message}, headers=headers)
         if r.content:
             try:
                 data = r.json()
                 id_sol = data.get('id_solicitud')
                 response = JSONResponse(content=data)
                 if id_request == id_sol:
                     print("son iguales")
                 else:
                     print("son diferentes")
                 print("post del front-end_enviando:",data)
                 return response
             except:
                 return JSONResponse(content={'message': 'No response body'})
         else:
             return JSONResponse(content={'message': 'No response body'})
     
     if __name__ == "__main__":
         import uvicorn
         dotenv.load_dotenv()
         ip_host = os.getenv("IP_HOST")
         uvicorn.run(app, host=ip_host, port=8000)
     ```

3. Cree la plantilla para renderizar su página html

   - Crear el codigo html, javascript y demás

     ```html
     <!DOCTYPE html>
     <html lang="en">
     
     <head>
         <meta charset="UTF-8">
         <meta name="viewport" content="width=device-width, initial-scale=1.0">
         <title>Request analisis App</title>
         <!-- Bootstrap CSS -->
         <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
         <link rel="icon" href="{{ url_for('static', path='favicon.ico') }}" type="image/x-icon">
     </head>
     
     <body>
         <div class="container mt-4">
             <div class="row">
                 <div class="col-md-6">
                     <form id="loginForm" style="display: none;">
                         <div class="form-group">
                             <label for="username">Username:</label>
                             <input type="text" class="form-control" id="username" required>
                             <label for="password">Password:</label>
                             <input type="password" class="form-control" id="password" required>
                             <label for="role">Role:</label>
                             <div class="form-check">
                                 <input class="form-check-input" type="radio" name="role" id="user" value="user" checked>
                                 <label class="form-check-label" for="user">
                                     User
                                 </label>
                             </div>
                             <div class="form-check">
                                 <input class="form-check-input" type="radio" name="role" id="analyst" value="analyst">
                                 <label class="form-check-label" for="analyst">
                                     Analyst
                                 </label>
                             </div>
                         </div>
                         <button type="button" class="btn btn-primary" onclick="login()">Login</button>
                     </form>
                     <button id="loginLogoutButton" type="button" class="btn btn-primary" style="display: block;"
                         onclick="toggleLoginLogout()">Login</button>
                 </div>
             </div>
             <div id="content" style="display: none;">
     
                 <div id="analisist" style="display: none;">
                     <input type="text" class="form-control" id="idInput" placeholder="Enter id_request">
                     <div class="mt-4">
                         <h2>Receive Message for analisis</h2>
                         <form id="receiveMessageFormAnalist">
                             <div class="form-group">
                                 <label for="message">Message:</label>
                                 <textarea class="form-control" id="analistMessageReceive" rows="5" readonly
                                     style="font-size: 24px;"></textarea>
                             </div>
                             <button id="receiveButtonAnalist" type="button" class="btn btn-info"
                                 onclick="receiveMessageAnalist()">Receive
                                 Message</button>
                         </form>
                     </div>
                     <div class="mt-4">
                         <h2>Send Message for analisys</h2>
                         <form id="sendMessageFormAnalist">
                             <div class="form-group">
                                 <label for="message">Message:</label>
                                 <input type="text" class="form-control" id="analisisMessageSend" required>
                             </div>
                             <button id="sendButtonAnalist" type="button" class="btn btn-info"
                                 onclick="sendMessageAnalist()">Send
                                 Message</button>
                         </form>
                     </div>
                 </div>
     
                 <div id="users" style="display: none;">
                     <label class="label label-primary" id="idLabel"></label>
                     <div class="mt-4">
                         <h2>Send Message for Analisis</h2>
                         <form id="sendMessageFormUser">
                             <div class="form-group">
                                 <label for="message">Message:</label>
                                 <input type="text" class="form-control" id="userMessageSend" required>
                             </div>
                             <button id="sendButtonUser" type="button" class="btn btn-info" onclick="sendMessageUser()">Send
                                 Message</button>
                         </form>
                     </div>
                     <div class="mt-4">
                         <h2>Receive final analysis result</h2>
                         <form id="receiveMessageFormUser">
                             <div class="form-group">
                                 <label for="message">Message:</label>
                                 <textarea class="form-control" id="userMessageReceive" rows="5" readonly
                                     style="font-size: 24px;"></textarea>
                             </div>
                             <button id="receiveButtonUser" type="button" class="btn btn-info"
                                 onclick="receiveMessageUser()">Receive
                                 Message</button>
                         </form>
                     </div>
                 </div>
             </div>
         </div>
     
         <!-- Bootstrap JS and dependencies -->
         <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
         <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.3/dist/umd/popper.min.js"></script>
         <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
     
         <script>
             let isLoggedIn = false;
             let shownMessages = new Set();
             //let messageInterval; 
     
             function toggleLoginLogout() {
                 const loginForm = document.getElementById("loginForm");
                 const loginLogoutButton = document.getElementById("loginLogoutButton");
                 const content = document.getElementById("content");
                 const users = document.getElementById("users");
                 const analisist = document.getElementById("analisist");
                 if (isLoggedIn) {
                     // Si el usuario está conectado, ocultar el formulario y cambiar el texto del botón a "Show Login"
                     loginForm.style.display = "none";
                     loginLogoutButton.textContent = "Login";
                     content.style.display = "none";
                     users.style.display = "none";
                     analisist.style.display = "none";
                     sessionStorage.removeItem('token');
                     //clearInterval(messageInterval);
                 } else {
                     // Si el usuario no está conectado, mostrar el formulario y cambiar el texto del botón a "Logout"
                     loginForm.style.display = "block";
                     loginLogoutButton.style.display = "none";
                     content.style.display = "block";
     
                 }
     
                 isLoggedIn = !isLoggedIn;
     
             }
     
             function login() {
                 const username = document.getElementById("username").value;
                 const password = document.getElementById("password").value;
                 const loginButton = document.getElementById("loginLogoutButton");
     
                 const encodedUsername = encodeURIComponent(username);
                 const encodedPassword = encodeURIComponent(password);
     
                 loginButton.disabled = true;
     
                 const url = `/login?username=${encodedUsername}&password=${encodedPassword}`;
     
                 fetch(url, {
                     method: 'POST',
                 })
                     .then(response => response.json())
                     .then(data => {
                         sessionStorage.setItem('token', data.access_token);
                         console.log(data.access_token);
                         //showContent();
                         document.getElementById("loginForm").style.display = "none";
                         const loginLogoutButton = document.getElementById("loginLogoutButton");
                         loginLogoutButton.textContent = "Logout";
                         loginLogoutButton.style.display = "block";
                         var role = document.querySelector('input[name="role"]:checked').value;
                         if (role == "user") {
                             document.getElementById("users").style.display = "block";
                             document.getElementById("analisist").style.display = "none";
                         } else {
                             document.getElementById("users").style.display = "none";
                             document.getElementById("analisist").style.display = "block";
                         }
                         isLoggedIn = true;
                         //messageInterval = setInterval(receiveMessage, 10000);
                     })
                     .catch((error) => {
                         console.error('Error:', error);
                     })
                     .finally(() => {
                         loginButton.disabled = false;
                     });
             }
     
             function sendMessageUser() {
                 const messageInput = document.getElementById("userMessageSend");
                 const message = messageInput.value;
                 const sendButton = document.getElementById("sendButtonUser");
     
                 sendButton.disabled = true;
                 var token = sessionStorage.getItem('token');
                 console.log('Sending message:', message);
                 const url = `/enviar_para_analisis`
                 fetch(url, {
                     method: 'POST',
                     headers: {
                         'Authorization': 'Bearer ' + token
                     },
                     body: JSON.stringify({message})
                 })
                     .then(response => {
                         if (!response.ok) {
                             throw new Error(`Solicitud:${response.status}`);
                         }
                         return response.json();
                     })
                     .then(data => {
                         console.log("Server response:", data);
                         document.getElementById("idLabel").textContent = data.id_solicitud;
                     })
                     .catch((error) => {
                         console.error('Error:', error);
                     })
                     .finally(() => {
                         sendButton.disabled = false;
                         messageInput.value = "";
                     });
             }
     
             function receiveMessageUser() {
                 const messageInput = document.getElementById("messageReceiveUser");
                 const receiveButton = document.getElementById("receiveButtonUser");
     
                 receiveButton.disabled = true;
                 var token = sessionStorage.getItem('token');
                 var id_request = sessionStorage.getItem('id_request');
                 if (id_request == null) {
                     id_request = "00000000-0000-0000-0000-000000000000";
                     return
                 }
                 const url = `/recibir_resultado_final_analisis/${id_request}`
                 fetch(url, {
                     method: 'GET',
                     headers: {
                         'Authorization': 'Bearer ' + token
                     }
                 })
                     .then(response => {
                         if (!response.ok) {
                             throw new Error(`Recepcion_resultado_final_análisis:${response.status}`);
                         }
                         return response.json();
                     })
                     .then(data => {
                         console.log("resultado final analisis response:", data);
                         messageInput.value = data.message;
                     })
                     .catch((error) => {
                         console.error('Error:', error);
                     })
                     .finally(() => {
                         receiveButton.disabled = false;
                     });
     
             }
     
             function sendMessageAnalist() {
                 const messageInput = document.getElementById("analisisMessageSend");
                 const message = messageInput.value;
                 const sendButton = document.getElementById("sendButtonAnalist");
     
                 sendButton.disabled = true;
                 var token = sessionStorage.getItem('token');
                 var id_request = sessionStorage.getItem('id_request');
                 console.log('Sending message:', message);
                 const url = `/enviar_resultado_del_analisis/${id_request}`
                 fetch(url, {
                     method: 'POST',
                     headers: {
                         'Authorization': 'Bearer ' + token
                     },
                     body: JSON.stringify({message})
                 })
                     .then(response => {
                         if (!response.ok) {
                             throw new Error(`Solicitud:${response.status}`);
                         }
                         return response.json();
                     })
                     .then(data => {
                         console.log("Server response:", data);
     
                     })
                     .catch((error) => {
                         console.error('Error:', error);
                     })
                     .finally(() => {
                         sendButton.disabled = false;
                         messageInput.value = "";
                     });
             }
     
             function receiveMessageAnalist() {
                 const messageInput = document.getElementById("analistMessageReceive");
                 const receiveButton = document.getElementById("receiveButtonAnalist");
                 const idInput = document.getElementById("idInput");
     
                 receiveButton.disabled = true;
                 var token = sessionStorage.getItem('token');
                 var id_request = sessionStorage.getItem('id_request');
                 if (id_request == null) {
                     if (idInput.value == null) {
                         alert("Debe ingresar un id de solicitud");
                         return
                     }
                     else {
                         id_request = idInput.value;
                     }
                     //id_request = "00000000-0000-0000-0000-000000000000";
                     //return
                 }
                 const url = `/recibir_mensaje_para_analisis/${id_request}`
                 fetch(url, {
                     method: 'GET',
                     headers: {
                         'Authorization': 'Bearer ' + token
                     },
                     timeout: 2000
                 })
                     .then(response => {
                         if (!response.ok) {
                             throw new Error(`Recepcion_para_analisis:${response.status}`);
                         }
                         return response.json();
                     })
                     .then(data => {
                         console.log("Server response:", data);
                         var decodedMessage = atob(data.mensaje);
                         console.log("Decoded message:", decodedMessage);
                         document.getElementById("idLabel").textContent = data.id_solicitud;
                         document.getElementById("analistMessageReceive").value = decodedMessage;
                     })
                     .catch((error) => {
                         console.error('Error:', error);
                         document.getElementById("analistMessageReceive").value = "No hay mensajes";
                     })
                     .finally(() => {
                         receiveButton.disabled = false;
                     });
             }
         </script>
     
     </body>
     
     </html>
     ```

4. Realice las comprobaciones 

   - Ejecute el programa en `front-end`

     `http://<ip>:8000`

     ![](img/05.png)

   - Seleccione Login y entre un usuario y una contraseña 

     ![](img/06.png)

   - Al autenticarse, deberá comenzar a recibir los mensajes de los otros participantes del chat

     ![](img/07.png)

   - Envie sus propios mensajes.

     ![](img/08.png)

     

# Conclusiones

Con esta práctica final, ha podido realizar un ciclo completo de utilización desde un `front-end`, consumiendo los servicios de una `apirest` con la integración de un back-end `RabbitMQ` y aplicando los patrones de **Colas de trabajo**.
