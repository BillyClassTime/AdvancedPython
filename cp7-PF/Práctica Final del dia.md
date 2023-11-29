# Práctica Final del día

## Automatización de pruebas para de FastAPI integrada con RabbitMQ, automatización avanzada y pruebas con Postman

### Escenario

Construiremos un entorno de mensajería similar al chat de WhatsApp, donde varios clientes acceden al servicio mediante autenticación con OAuth2 y JWT. 

Los mensajes son gestionados por un front-end implementado con FastAPI y Jinja2, mientras que el middleware utiliza una API RESTful con FastAPI y aio_pika para gestionar la comunicación con el backend  RabbitMQ, que utilizará colas duraderas para asegurar la persistencia de los mensajes.

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
                     queue = await channel.declare_queue('mis_mensajes',durable=True)
                     await channel.default_exchange.publish(
                         aio_pika.Message(body=mensaje.encode(),
                                          delivery_mode=aio_pika.DeliveryMode.PERSISTENT, # El mensaje se guarda en disco
                                          # Si no se extablece expiration, el mensaje no caduca
                                          expiration=360000), # Tiempo en milisegundos antes de que el mensaje
                         routing_key='mis_mensajes',timeout=30
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
                     queue = await channel.declare_queue('mis_mensajes',durable=True)
                     async def on_message(message):
                         try:
                             #async with message.process(): # El mensaje se marca como procesado
                             mensajes_recibidos.append(message.body.decode())
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

4. Gestionar las rutas de su APIRest

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

   - Cree las rutas y cumpla con los estandares

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
         "http://localhost:15000",
         "http://localhost:8000",
         "http://127.0.0.1:8000"
         ]
     
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

6. Implemente el fichero principal del proyecto

   - Implemente el punto inicial

     ```python
     from app_core.initializer import app
     
     if __name__ == "__main__":
         import uvicorn
         uvicorn.run(app, host="127.0.0.1", port=15000)
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
     
     | Descripción                     | comando                                          |
     | ------------------------------- | ------------------------------------------------ |
     | Listar todas las colas          | rabbitmqadmin list queues                        |
     | Ver el tamaño de una cola       | rabbitmqadmin get queue=name_de_la_cola          |
     | Listar los mensajes de una cola | rabbitmqadmin get queue=name_de_la_cola count=N* |
     | Purgar una cola                 | rabbitmqadmin purge queue name=name_de_la_cola   |
     | Listar Exchanges                | rabbitmqadmin list exchanges                     |
     | Listar Vinculos                 | rabbitmqadmin list bindings                      |
     | Listar VHost                    | rabbitmqadmin list vhosts                        |
     | Listar Usuarios                 | rabbitmqadmin list users                         |
     
     `*N` mostrará los N mensajes desde el último hasta el primero.
     
     Cada comando debe ser utilizado con el usuario y contraseña de acceso a rabbit asi:
     
     `rabbitmqadmin -u usuario -p contraseña <comando>`
     
     ejemplo:
     
     `rabbitmqadmin -u usuario -p pasword list queues`
     
     > **Nota**: Si utiliza `docker` en un contenedor docker puede adjuntar la sesion del contenedor desde su linea de comandos así: `docker exec -it my-rabbit /bin/bash`, donde `my-rabbit` es el nombre de su contenedor `docker` en ejecución.
     
     > **Nota:** Antes de iniciar sus pruebas recuerde que es una buena idea comenzar con un `Estado Inicial` donde todo este a cero desde un comienzo, considere utilizar los comandos anteriores para purgar las colas que vayan a participar en sus pruebas.
     
     Listado de comandos disponibles desde la linea de comandos complementarios a `rabbitmqadmin`, recuerde que estas son accedidos con usuarios con privilegios de administración.
     
     | Comando              | Descripción                                                  |
     | -------------------- | ------------------------------------------------------------ |
     | rabbitmqctl          | Gestión del servicio y tareas generales del operador         |
     | rabbitmq-diagnostics | Verificación de salud y estbilidad de RabbitMQ               |
     | rabbitmq-plugins*    | Para la gestión de complementos                              |
     | rabbitmq-queues      | Para tareas de mantenimiento en colas, especialmente colas de cuórum ** |
     | rabbitmq-upgrade     | Para tareas relacionadas con actualizaciones                 |
     
     `*` Recuerde que en la sesión 2, utilizamos `rabbitmq-plugins enable rabbitmq_management` para activar la interfaz web de RabbitMQ.
     
     `**` Colas de cuórum o colas en balanceo de carga.
   
   
   - Crear los casos de pruebas con éxito y con error
   
     ```python
     # test/unit_integration.py
     
     import unittest
     import asynctest
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
             cls.client = TetstClient(app)
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
             response_publish = self.client.post(f"/publicar/{mensaje}", headers={"Authorization": f"Bearer {self.token}})
             self.assertEqual(response_publish.status_code, 200)
             self.assertIn("mensaje", response_publish.json())
     
             # Test consuming the published message
             response_consume = self.client.get("/consumir", headers={"Authorization": f"Bearer {self.token}"})
             self.assertEqual(response_consume.status_code, 200)
             self.assertIn("mensajes", response_consume.json())
             self.assertIn("TestMessage", response_consume.json()["mensajes"])
     
     if __name__ == "__main__":
         unittest.main() 
     ```
     
   - Ejecutar las pruebas
   
     ```powershell
     py -m unittest test\unit_integration.py -v
     test_publish_consume_message_flow (test.unit_integration.TestRabbitMQRoutes) ... ok
     test_login (test.unit_integration.TestSecurityRoutes) ... ok
     ```
   
     > **Nota:** Si la pruebas son correctas puede continuar

### 2. Organización de Colecciones

1. Crear el entorno

   Cree su entorno para albergar las colecciones

   `Sesion7-PF`

2. Cree las colecciones

   Cree la colección

   ```bash
   FastAPIFRONT-MIDL-Backnd
   ```
   
3. Crear las variables de entorno

   | Variable     | Initial Value          |
   | ------------ | ---------------------- |
   | api_url      | http://localhost:15000 |
   | username_api | su usuario           |
   | password_api | su contraseña        |
   
4. Crear Solicitudes

   ```
   FastAPIFRONT-MIDL-Backnd
   ├─── POST login
   ├─── POST Send Message
   ├─── GET Receive Mensaje
   ```
   
   - **Obtener el token**
   
     `POST` **login**
   
     **url** `{{api_url}}/token`
   
     ```
     Params:
     username {{username_api}}
     password {{password_api}}
     ```
     
   - **Enviar Mensaje**
   
     `POST` **Send Message**
   
     **url** `{{api_url}}/publicar/Mario:Hola desde Madrid`

     ```
     Authorization:
     Bearer Token {{token}}
     ```
   
     **Nota:** Para enviar esta solicitud debe recuperar el `token` de respuesta de la solicitud de `login` y ponerlo en la autorización, mas adelante automatizará este paso.
   
   - **Recibir Mensajes**
   
     `GET` **Receive Message**
   
     **url** `{{api_url}}/consumir`
     
     ```
     Authorization:
     Bearer Token {{token}}
     ```
     
     **Nota:** Para enviar esta solicitud debe recuperar el `token` de respuesta de la solicitud de `login` y ponerlo en la autorización, mas adelante automatizará este paso.

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
   
     ![](img/02.png)
   
   - Revise el resultado
   
     ![](img/03.png)
   
   - Revise el resumen detallado
   
     ![](img\04.png)



### 2. Entorno front-end gestion del chat

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
     from fastapi import FastAPI, Request, Response
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
     
     @app.post("/sendmessage/{message}")
     async def sendmessage(request: Request, message: str):
         token = request.headers.get('Authorization')  # Recupera el token de las cabeceras
         #print(f"enviando:{token}")
         if not token:
             return JSONResponse(content={'message': 'No token'})
         headers = {'Authorization': token}
         decoded_token = jwt.decode(token.split(' ')[1], options={"verify_signature": False})
         user = decoded_token['sub']
         message = f"{user}: {message}"
         async with httpx.AsyncClient() as client:
             r = await client.post(f'{url_base}/publicar/{message}', headers=headers)
         if r.content:
             try:
                 data = r.json()
                 return JSONResponse(content=data)
             except:
                 return JSONResponse(content={'message': 'No response body'})
         else:
             return JSONResponse(content={'message': 'No response body'})
         
     @app.get("/receivemessage")
     async def receivemessage(request: Request):
         token = request.headers.get('Authorization')  # Recupera el token de las cabeceras
         #print(f"recibiendo:{token}")
         if not token:
             return JSONResponse(content={'message': 'No token'})
         headers = {'Authorization': token}
         async with httpx.AsyncClient() as client:
             r = await client.get(f'{url_base}/consumir', headers=headers)
         if r.content:
             try:
                 data = r.json()
                 print(data)
                 return JSONResponse(content=data)
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

   ```html
   <!DOCTYPE html>
   <html lang="en">
   
   <head>
       <meta charset="UTF-8">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>Chat App</title>
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
                       </div>
                       <button type="button" class="btn btn-primary" onclick="login()">Login</button>
                   </form>
                   <button id="loginLogoutButton" type="button" class="btn btn-primary" style="display: block;"
                       onclick="toggleLoginLogout()">Login</button>
               </div>
           </div>
   
           <div id="content" style="display: none;">
               <div class="mt-4">
                   <h2>Receive Message</h2>
                   <form id="receiveMessageForm">
                       <div class="form-group">
                           <label for="message">Message:</label>
                           <textarea class="form-control" id="messageReceive" rows="5" readonly
                               style="font-size: 24px;"></textarea>
                       </div>
                       <button id="receiveButton" type="button" class="btn btn-info" onclick="receiveMessage()">Receive
                           Message</button>
                   </form>
               </div>
               <div class="mt-4">
                   <h2>Send Message</h2>
                   <form id="sendMessageForm">
                       <div class="form-group">
                           <label for="message">Message:</label>
                           <input type="text" class="form-control" id="messageSend" required>
                       </div>
                       <button id="sendButton" type="button" class="btn btn-info" onclick="sendMessage()">Send
                           Message</button>
                   </form>
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
           let messageInterval; 
   
           function toggleLoginLogout() {
               const loginForm = document.getElementById("loginForm");
               const loginLogoutButton = document.getElementById("loginLogoutButton");
               const content = document.getElementById("content");
   
               if (isLoggedIn) {
                   // Si el usuario está conectado, ocultar el formulario y cambiar el texto del botón a "Show Login"
                   loginForm.style.display = "none";
                   loginLogoutButton.textContent = "Login";
                   content.style.display = "none";
                   sessionStorage.removeItem('token');
                   clearInterval(messageInterval);
               } else {
                   // Si el usuario no está conectado, mostrar el formulario y cambiar el texto del botón a "Logout"
                   loginForm.style.display = "block";
                   loginLogoutButton.style.display = "none";
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
                       document.getElementById("content").style.display = "block";
                       document.getElementById("loginForm").style.display = "none";
                       const loginLogoutButton = document.getElementById("loginLogoutButton");
                       loginLogoutButton.textContent = "Logout";
                       loginLogoutButton.style.display = "block";
                       isLoggedIn = true;
                       messageInterval = setInterval(receiveMessage, 10000);
                   })
                   .catch((error) => {
                       console.error('Error:', error);
                   })
                   .finally(() => {
                       loginButton.disabled = false;
                   });
           }
   
           function sendMessage() {
               const messageInput = document.getElementById("messageSend");
               const message = messageInput.value;
               const sendButton = document.getElementById("sendButton");
   
               sendButton.disabled = true;
               var token = sessionStorage.getItem('token');
               console.log(token);
               const url = `/sendmessage/${message}`;
               fetch(url, {
                   method: 'POST',
                   headers: {
                       'Authorization': 'Bearer ' + token
                   }
               })
                   .then(response => response.json())
                   .then(data => {
                       console.log(data);
                   })
                   .catch((error) => {
                       console.error('Error:', error);
                   })
                   .finally(() => {
                       sendButton.disabled = false;
                       messageInput.value = "";
                   });
           }
   
           function receiveMessage() {
               const receiveButton = document.getElementById("receiveButton");
   
               receiveButton.disabled = true;
   
               var token = sessionStorage.getItem('token');
               console.log(token);
               const url = '/receivemessage';
               fetch(url, {
                   method: 'GET',
                   headers: {
                       'Authorization': 'Bearer ' + token
                   }
               })
                   .then(response => response.json())
                   .then(data => {
                       console.log(data);
                       const textarea = document.getElementById('messageReceive');
                       if (data.mensajes) {
                           data.mensajes.forEach(message => {
                               if (!shownMessages.has(message)) {
                                   textarea.value += message + '\n';
                                   shownMessages.add(message);
                               }
                           });
                       }
                   })
                   .catch((error) => {
                       console.error('Error:', error);
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

   - Revise que sus mensajes también son mostrados en los mensajes del chat.

     ![](img/09.png) 

# Conclusiones

Con esta práctica final, ha podido realizar un ciclo completo de utilización desde un `front-end`, consumiendo los servicios de una `apirest` con la integración de un back-end `RabbitMQ`
