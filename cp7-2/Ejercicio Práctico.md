# Ejercicio Práctico

## Seguridad y autenticación FastAPI, RabbitMQ y Postman

### 1. Configuración de Entorno

1. Crear la estructura de su proyecto

   ```powershell
   My Proyect:
   ├───api
   │   └───routes
   │       └─── __init__.py
   │       └─── rabbitMQRoutes.py
   │       └─── securityRoutes.py
   ├───app_core
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
     ```

   - cree las variables del entorno en su fichero .env

     ```python
     RABBITMQ_USERNAME=usuario
     RABBITMQ_PASSWORD=clave
     RABBITMQ_HOST=url a rabbitMQ
     RABBITMQ_VHOST=\
     RABBITMQ_PORT=5672
     SECRET_KEY = "mikeysecreta"
     ALGORITHM = "HS256"
     ACCESS_TOKEN_EXPIRE_MINUTES = 30
     USERNAME = "Billy"
     PASSWORD = "P4w0rd1234"
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
      from dotenv import load_dotenv
      
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
              self.connection = None
      
          async def connect(self):
              try:
                  self.connection = await aio_pika.connect_robust(self.connection_string)
              except aio_pika.exceptions.AMQPError as e:
                  raise RabbitMQError(f"Error al conectar con RabbitMQ: {str(e)}")
      
          async def publish_message(self, mensaje):
              if not self.connection:
                  await self.connect()
              try:
                  async with self.connection.channel() as channel:
                      queue = await channel.declare_queue('mi_cola',durable=True)
                      await channel.default_exchange.publish(
                          aio_pika.Message(body=mensaje.encode(),
                                           delivery_mode=aio_pika.DeliveryMode.PERSISTENT, # El mensaje se guarda en disco
                                           # Si no se extablece expiration, el mensaje no caduca
                                           expiration=360000), # Tiempo en milisegundos antes de que el mensaje
                          routing_key='mi_cola',timeout=30
                      )
              except aio_pika.exceptions.AMQPError as e:
                  errorMensaje="Error al publicar mensaje en RabbitMQ"
                  print(f"{errorMensaje}: {str(e)}")
                  raise RabbitMQError(f"{errorMensaje}: {str(e)}")
      
          async def consume_messages(self, callback):
              if not self.connection:
                  await self.connect()
              try:
                  mensajes_recibidos = []
                  async with self.connection.channel() as channel:
                      queue = await channel.declare_queue('mi_cola',durable=True)
                      async def on_message(message):
                          try:
                              async with message.process(): # El mensaje se marca como procesado
                                  mensajes_recibidos.append(message.body.decode())
                                  #await message.ack() # Confirmar que el mensaje se ha procesado correctamente
                                  #automaticamente se confirma el mensaje	al salir de la funcion
                                  #no hace falta poner el await message.ack()
                          except Exception as e:
                              raise RabbitMQError(f"Error al procesar mensaje: {str(e)}")
                      await queue.consume(on_message)
                  await callback(mensajes_recibidos)
              except aio_pika.exceptions.AMQPError as e:
                  errorMensaje="Error al consumir mensaje en RabbitMQ"
                  raise RabbitMQError(f"{errorMensaje}: {str(e)}")
      
          async def close(self):
              if self.connection:
                  await self.connection.close()
      ```
      
      
   
3. Crear Excepciones personalizadas

   - Cree las excepciones personalizadas del proyecto

     `rabbitMQException.py`
     
     ```python
     class RabbitMQError(Exception):
         def __init__(self, mensaje):
             super().__init__(mensaje)
     ```
     
     `customExceptions.py`
     
     ```python
     from fastapi import HTTPException, status
     
     class customException(HTTPException):
         def __init__(self, detail: str):
             super().__init__(
                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                 detail=detail)
     ```
     
     

4. Gestionar las rutas de su APIRest

   - Crear la ruta de gestión de seguridad 

     ```python
     from datetime import timedelta
     from fastapi import APIRouter, HTTPException
     from services.securityServices import create_jwt_token, get_current_user,config
     
     router = APIRouter()
     
     @router.post("/token")
     def login(username: str, password: str):
         # Aquí deberías realizar la autenticación del usuario y verificar las credenciales
         # Por simplicidad, este ejemplo asume que el usuario y la contraseña son correctos
         expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
         access_token = create_jwt_token(data={"sub": username}, expires_delta=expires)
         return {"access_token": access_token, "token_type": "bearer"}
     ```

     

   - Cree las rutas y cumpla con los estándares integrados a la seguridad

     ```python
     from fastapi import APIRouter, Depends, HTTPException
     from fastapi.responses import RedirectResponse
     
     from services.rabbitMQServices import RabbitMQ
     from services.securityServices import get_current_user
     
     route = APIRouter() 
     
     @route.get("/consumir")
     async def consumir(str=Depends(get_current_user)):
         mensaje_recibidos = None
         rabbitmq = None
         try:
             async def callback(mensajes):
                 #print(f"Recibidos mensajes: {mensajes}")
                 nonlocal mensaje_recibidos
                 mensaje_recibidos = mensajes
             rabbitmq = RabbitMQ()
             await rabbitmq.connect()
             await rabbitmq.consume_messages(callback)
             if mensaje_recibidos is not None and len(mensaje_recibidos) > 0:
                 return {"mensajes": mensaje_recibidos}
             else:
                 raise HTTPException(status_code=404, detail="No hay mensajes en la cola")
         except HTTPException as he:
             print(f"Excepcion HTTP consumiendo el mensaje: {he.detail}")
             return {"mensajes": []}
         finally:
             if rabbitmq is not None:
                 await rabbitmq.close()
     
     @route.post("/publicar/{mensaje}", response_model=dict)
     async def publicar_mensaje(mensaje: str, current_user: str=Depends(get_current_user)):
         rabbitmq = None
         try:
             #print(f"Publicando mensaje: {mensaje}")
             if current_user is None:
                 raise HTTPException(status_code=401, detail=f"usuario:{current_user}, no autorizado")
             #else:
             #    print(f"Usuario autenticado: {current_user}")
             rabbitmq = RabbitMQ()
             await rabbitmq.connect()
             await rabbitmq.publish_message(mensaje)
             return {"mensaje": f"Mensaje '{mensaje}' publicado correctamente en la cola."}
         except Exception as e:
             print(f"Excepción publicando el mensaje:{str(e)}")
             raise HTTPException(status_code=500, detail=f"publicando el mensaje:{str(e)}")
         finally:
             if rabbitmq is not None:
                 await rabbitmq.close()
     
     @route.get("/", response_class=RedirectResponse, status_code=302,include_in_schema=False)
     async def redirect_to_docs():
         return "/docs"        
     ```

5. Implementar el Inicializador

   - Cree el punto de conexión entre la entrada inicial y los demás componentes del proyecto

     ```python
     from api.routes import rabbitMQRoutes
     from api.routes import securityRoutes
     from fastapi import FastAPI, HTTPException
     from custom_exceptions.customExceptions import customException
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
     
     app.include_router(rabbitMQRoutes.route)
     app.include_router(securityRoutes.router)
     ```

6. Implemente el fichero principal del proyecto

   - Implemente el punto inicial

     ```python
     from app_core.initializer import app
     
     if __name__ == "__main__":
         import uvicorn
         uvicorn.run(app, host="127.0.0.1", port=10500)
     ```


7. Pruebe la aplicación en Open API

   - Este proyecto tiene una redirección desde la ruta raiz `\` a `\docs`, inicie su navegador y ponga: `http:\\localhost:10500` 

     ![01](img/01.png)
     
     Recuerde que RabbitMQ debe estar en ejecución, y su url deberá estar en: `RABBITMQ_HOST=url a rabbitMQ`, confirme que su servidor esta accesible antes de continuar con las pruebas.
     
     > **Nota:** Si puede publicar y consumir mensajes, siga adelante

8. Pruebas unitarias

   - Crear los casos de pruebas con éxito y con error

     ```python
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
     ```
   
   - Ejecutar las pruebas
   
     ```powershell
     py -m unittest test\unit_integration.py -v
     test_consume_messagesMQ (test.unit_integration.TestRabbitMQIntegration) ... ok
     test_publish_messageMQ (test.unit_integration.TestRabbitMQIntegration) ... ok
     test_consumir_mensajeAPI (test.unit_integration.TestRoutes) ... ok
     test_login (test.unit_integration.TestRoutes) ... ok
     test_publicar_mensajeAPI (test.unit_integration.TestRoutes) ... ok
     test_publicar_mensaje_sin_autenticacionAPI (test.unit_integration.TestRoutes) ... ok
     ```
     
     > **Nota:** Si la pruebas son correctas puede continuar



### 2. Organización de Colecciones

1. Crear el entorno

   Cree su entorno para albergar las colecciones

   `OAuth2JWT`

2. Cree las colecciones

   Cree las colecciones que albergarán sus solicitudes

   ```
   FastAPIRabbitMQOAuth2JWT
   ```
   
3. Crear las variables de entorno

   | Variable     | Initial Value          |
   | ------------ | ---------------------- |
   | api_url      | http://localhost:10500 |
   | username_api | <su usuario>           |
   | password_api | <su contraseña>        |

4. Crear Solicitudes

   ```
   FastAPIRabbitMQOAuth2JWT
   ├─── POST get_token
   ├─── POST publicar
   ├─── GET consumir
   ```
   
   - **get_token**
   
     `POST` **get_token**
   
     **url** `{{api_url}}/token`
   
     ```json
     Params:
     username {{username_api}}
     password {{password_api}}
     ```
   
   - **publicar**
   
     `POST` **publicar**
   
     **url** `{{api_url}}/publicar/NuevoMensaje`

     ```
     Authorization:
     <TOKEN>
     ```
   - **consumir**
     `GET` **consumir**
   
     **url** `{{api_url}}/consumir`
     
     ```
     Authorization
     <TOKEN>
     ```

### 4. Automatización de solicitudes

1. Cree los script de automatización de pruebas para corroborar cada una de las solicitudes del proyecto. Postman gestiona en una única colección, la gestión directa hacia el servidor `RabbitMQ` y a su `API Rest`

   - **Test** en **get_token** `POST` **get_token**

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
   - **Test** en **publicar** `POST` **publicar**
   
     ```javascript
     pm.test("Obtener token", function () {
       pm.response.to.have.status(200);
     });
     ```
   
   - **Auth** en **publicar** 
     
     ```json
     {{token}}
     ```
     
   - **Tests** en **consumir** `GET` **consumir**
   
     ```javascript
     pm.test("Obtener token", function () {
       pm.response.to.have.status(200);
     });
     ```
     
   - **Auth** en **consumir**
   
     ```json
     {{token}}
     ```
   
     
   
   ### 5. Revision de pruebas
   
   - Ejecute las pruebas de la colección
   
     ![](img/02.png)
   
   - Revise el resultado
   
     ![](img/03.png)
   
   - Revise el resumen detallado
   

  ![](img\04.png)



# Conclusiones

En este ejercicio a conseguido programar una `APIRest` que gestiona solicitudes hacia `RabbitMQ` siguiendo  las mejores prácticas de seguridad y otros principios de buen diseño, por ultimo ha realizado la automatización de pruebas de integración con `Postman` para controlar su `APIRest` con la autenticación y autorización OAuth2 y JWT.
