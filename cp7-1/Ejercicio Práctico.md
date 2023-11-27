# Ejercicio Práctico

## Automatización de pruebas de integración para mensajes con Postman

### 1. Configuración de Entorno

1. Crear la estructura de su proyecto

   ```powershell
   My Proyect:
   ├───api
   │   └───routes
   │       └─── __init__.py
   |            manageRoutes.py
   ├───app_core
   │   └───__init__.py
   │       initializer.py
   ├───custom_exceptions
   │   └───__init__.py
   │       rabbitMQExceptions.py
   ├───services
   │   └───__init__.py
   │       manageServices.py
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
      pip install fastapi uvicorn aio_pika python-dotenv httpx
   
   
   - cree las variables del entorno en su fichero .env
     
     ```python
     RABBITMQ_USERNAME=usuario
     RABBITMQ_PASSWORD=clave
     RABBITMQ_HOST=url a rabbitMQ
     RABBITMQ_VHOST=\
     RABBITMQ_PORT=5672
     ```
2. Crear los servicios
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

     ```python
     class RabbitMQError(Exception):
         def __init__(self, mensaje):
             super().__init__(mensaje)
     ```

4. Gestionar las rutas de su APIRest

   - Cree las rutas y cumpla con los estandares

     ```python
     from fastapi import APIRouter, HTTPException
     from services.manageServices import RabbitMQ
     from fastapi.responses import JSONResponse, RedirectResponse
     
     class CustomAPIRouter(APIRouter):
         async def exception_handler(self, request, exc):
             return JSONResponse(status_code=500, content={"message": "Error interno del servidor"})
     
     route = CustomAPIRouter() 
     
     @route.get("/consumir")
     async def consumir():
         mensaje_recibidos = None
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
             #curl -X GET "http://localhost:puerto/consumir"
         except HTTPException as e:
             raise e
         except Exception as e:
             raise HTTPException(status_code=500, detail=f"consumiendo el mensaje:{str(e)}") 
         finally:
             await rabbitmq.close()
     
     @route.post("/publicar/{mensaje}", response_model=dict)
     async def publicar_mensaje(mensaje: str):
         try:
             rabbitmq = RabbitMQ()
             await rabbitmq.connect()
             await rabbitmq.publish_message(mensaje)
             return {"mensaje": f"Mensaje '{mensaje}' publicado correctamente en la cola."}
             #curl -X POST "http://localhost:puerto/publicar/hola"
         except HTTPException as e:
             raise e
         except Exception as e:
             raise HTTPException(status_code=500, detail=f"publicando el mensaje:{str(e)}")
         finally:
             await rabbitmq.close()
     
     @route.get("/", response_class=RedirectResponse, status_code=302,include_in_schema=False)
     async def redirect_to_docs():
         return "/docs"  
     ```

5. Implementar el Inicializador

   - Cree el punto de conexión entre el inicio principal y los demás componentes del proyecto

     ```python
     from api.routes import manageRoutes as RabbitMQRoutes
     from fastapi import FastAPI
     
     app = FastAPI()
     
     app.include_router(RabbitMQRoutes.route)
     ```

6. Implemente el fichero principal del proyecto

   - Implemente el punto inicial

     ```python
     from app_core.initializer import app
     
     if __name__ == "__main__":
         import uvicorn
         uvicorn.run(app, host="127.0.0.1", port=9525)
     ```


7. Pruebe la aplicación en Open API

   - Este proyecto tiene una redirección desde la ruta raiz `\` a `\docs`, inicie su navegador y ponga: `http:\\localhost:9525` 

     ![01](img/01.png)
     
     Recuerde que RabbitMQ debe estar en ejecución, y su url deberá estar en: `RABBITMQ_HOST=url a rabbitMQ`, confirme que su servidor esta accesible antes de continuar con las pruebas.
     
     > **Nota:** Si puede publicar y consumir mensajes, siga adelante

8. Pruebas unitarias

   - Crear los casos de pruebas con exito y co error

     ```python
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
     ```

   - Ejecutar las pruebas

     ```powershell
     py -m unittest test\unit_integration.py -v
     test_consumir (test.unit_integration.TestManageRoutes) ... ok
     test_consumir_sin_mensajes (test.unit_integration.TestManageRoutes) ... ok
     test_publicar_mensaje (test.unit_integration.TestManageRoutes) ... ok
     test_publicar_mensaje_negativo (test.unit_integration.TestManageRoutes) ... ok
     test_redirect_to_docs (test.unit_integration.TestManageRoutes) ... ok
     ```

     > **Nota:** Si la pruebas son correctas puede continuar



### 2. Organización de Colecciones

1. Crear el entorno

   Cree su entorno para albergar las colecciones

   `FastAPI_RabbitMQ`

2. Cree las colecciones

   Cree las colecciones con la siguiente jerarquía

   ```
   FastAPIRabbitMQ Integration Test
   ├───01-Estado Inicial
   ├───02-Publicar Mensajes
   ├───03-Consumir Mensajes
   ```

3. Crear las variables de entorno

   | Variable           | Initial Value                                    |
   | ------------------ | ------------------------------------------------ |
   | api_url            | http://localhost:9525                            |
   | rabbitmq_username  | usuario RabbitMQ administrador                   |
   | rabbitmq_password  | contraseña del usuario administrador de RabbitMQ |
   | rabbitmq_host      | url al servidor RabbitMQ                         |
   | rabbitmq_amqp_port | 5672                                             |
   | rabbitmq_queue     | mi_cola                                          |
   | rabbitmq_http_port | 15672                                            |
   | rabbitmq_vhost     | %2F                                              |

4. Crear Solicitudes

   ```
   FastAPIRabbitMQ Integration Test
   ├───01-Estado Inicial
   │   └───DEL purgarCola
   │   └───PUT 01-Crear Nueva Cola
   │   └───DEL 02-Borrar Cola
   ├───02-Publicar Mensajes
   │   └───POST Publicar Mensaje
   ├───03-Consumir Mensajes
   │   └───GET Consumir Mensaje
   ```

   - **01-Estado Inicial**

     `DEL` **purgarCola**

     **url** `http://{{rabbitmq_host}}:{{rabbitmq_http_port}}/api/queues/{{rabbitmq_vhost}}/{{rabbitmq_queue}}/contents`

     ```
     Authorization:
     Basic Auth:
     Username {{rabbitmq_username}}
     Password {{rabbitmq_password}}
     ```

     `PUT` **01-Crear Nueva Cola**

     **url**`http://{{rabbitmq_host}}:{{rabbitmq_http_port}}/api/queues/{{rabbitmq_vhost}}/{{rabbitmq_queue}}`
     ```
     Authorization:
     Basic Auth:
     Username {{rabbitmq_username}}
     Password {{rabbitmq_password}}
     ```
     
     `DEL` **02-Borrar Cola**
     
     **url** `http://{{rabbitmq_host}}:{{rabbitmq_http_port}}/api/queues/{{rabbitmq_vhost}}/{{rabbitmq_queue}}`
     
     
   
   - **02-Publicar Mensajes**
   
     `POST` **Publicar Mensaje**
   
     **url** `{{api_url}}/publicar/NuevoMensaje`
   
     
   
   - 03-Consumir Mensajes
   
     `GET` **Consumir Mensaje**
   
     **url** `{{api_url}}/consumir`



### 3. Preparación del Estado Inicial

1. En las solicitudes de la carpeta `01-Estado Inicial` ejecute las solicitudes para confirmar que llega al servidor `RabbitMQ`y que puede `purgar`, `crear` y `borrar` las **colas** correctamente.

   > **Nota:** Si puede gestionar el estado inicial, podrá dejar el servidor RabbitMQ en un estado óptimo para iniciar las pruebas y la depuración de su proyecto.



### 4. Automatización de solicitudes

1. Cree los script de automatización de pruebas para corroborar cada una de las solicitudes del proyecto. Postman gestiona en una única colección, la gestión directa hacia el servidor `RabbitMQ` y a su `API Rest`

   - **Test** en **01-Estado Inicial** `DEL` **purgarCola**

     ```javascript
     // DEL purgarCola
     // Configuración de variables
     const rabbitmqHost = pm.environment.get("rabbitmq_host");
     const rabbitmqHttpPort = pm.environment.get("rabbitmq_http_port");
     const rabbitmqVhost = pm.environment.get("rabbitmq_vhost");
     const rabbitmqQueue = pm.environment.get("rabbitmq_queue");
     const rabbitmqUser = pm.environment.get("rabbitmq_username");
     const rabbitmqPassword = pm.environment.get("rabbitmq_password");
     
     // Configurar la solicitud para purgar la cola (DELETE)
     const purgeQueueUrl = `http://${rabbitmqHost}:${rabbitmqHttpPort}/api/queues/${rabbitmqVhost}/${rabbitmqQueue}/contents`;
     pm.request.url = purgeQueueUrl;
     pm.request.method = "DELETE";
     pm.request.body = {};
     pm.request.headers.add({ key:'Authorization', value: `Basic ${btoa(rabbitmqUser + ':' + rabbitmqPassword)}` });
     
     // Log para verificar la URL de la solicitud de purga
     console.log("Test-00- URL para purgar cola: " + purgeQueueUrl);
     
     // Verificar que la cola se halla purgado correctamente
     pm.test("Test - Cola purgada correctamente", function () {
         const statusCode = pm.response.code;
         pm.expect(statusCode).to.be.oneOf([201, 204]);
     });
     ```

   - **Test** en **01-Estado Inicial** `PUT` **01-Crear Nueva Cola**

     ```javascript
     // Configuración de variables
     const rabbitmqHost = pm.environment.get("rabbitmq_host");
     const rabbitmqHttpPort = pm.environment.get("rabbitmq_http_port");
     const rabbitmqVhost = pm.environment.get("rabbitmq_vhost");
     const rabbitmqQueue = pm.environment.get("rabbitmq_queue");
     const rabbitmqUser = pm.environment.get("rabbitmq_username");
     const rabbitmqPassword = pm.environment.get("rabbitmq_password");
     
     // Configurar la solicitud para crear la cola (PUT)
     const createQueueUrl = `http://${rabbitmqHost}:${rabbitmqHttpPort}/api/queues/${rabbitmqVhost}/${rabbitmqQueue}`;
     pm.request.url = createQueueUrl;
     pm.request.method = "PUT";
     pm.request.body = {
         mode: "raw",
         raw: JSON.stringify({ durable: true }) // Puedes ajustar otras configuraciones aquí
     };
     pm.request.headers.add({ key:'Authorization', value: `Basic ${btoa(rabbitmqUser + ':' + rabbitmqPassword)}` });
     
     // Log para verificar la URL de la solicitud de creación de cola
     console.log("Test-01-URL para crear cola: " + createQueueUrl);
     
     // Verificar que la cola se haya creado correctamente
     pm.test("Test-01-Cola creada correctamente", function () {
         const statusCode = pm.response.code;
         pm.expect(statusCode).to.be.oneOf([201, 204]);
     });
     ```

   - **Tests** en **01-Estado Inicial** `DEL` **02-Borrar Cola**

     ```javascript
     // Configuración de variables
     const rabbitmqHost = pm.environment.get("rabbitmq_host");
     const rabbitmqHttpPort = pm.environment.get("rabbitmq_http_port");
     const rabbitmqVhost = pm.environment.get("rabbitmq_vhost");
     const rabbitmqQueue = pm.environment.get("rabbitmq_queue");
     const rabbitmqUser = pm.environment.get("rabbitmq_username");
     const rabbitmqPassword = pm.environment.get("rabbitmq_password");
     
     // Construir la URL para eliminar la cola
     const deleteQueueUrl = `http://${rabbitmqHost}:${rabbitmqHttpPort}/api/queues/${rabbitmqVhost}/${rabbitmqQueue}`;
     
     // Configurar la solicitud para eliminar la cola
     pm.request.url = deleteQueueUrl;
     pm.request.method = "DELETE";
     pm.request.headers.add({ key:'Authorization', value: `Basic ${btoa(rabbitmqUser + ':' + rabbitmqPassword)}` });
     
     console.log("Test-02-Cola de RabbitMQ borrada ")
     pm.test("Test-02-Cola borrada correctamente", function () {
         pm.response.to.have.status(204);
     });
     ```

   - **Tests** en **02-Publicar Mensajes** `POST` **Publicar Mensaje**

     ```javascript
     pm.test("Test Publicar Mensaje", function () {
       pm.response.to.have.status(200);
     });
     ```

     

   - **Tests** en **03-Consumir Mensajes** `GET` **Consumir Mensaje**

     ```javascript
     pm.test("Test Publicar Mensaje", function () {
       pm.response.to.have.status(200);
     });
     ```

     

   ### 5. Revision de pruebas

   - Ejecute las pruebas de la colección

     ![](img/02.png)

   - Revise el resultado

     ![](img/03.png)

   - Revise el resumen detallado

     ![](img\04.png)



# Conclusiones

En este ejercicio a conseguido programar una `APIRest` que gestiona solicitudes hacia `RabbitMQ` siguiendo muchos de las mejores prácticas y por ultimo realizado la automatización de pruebas de integración con `Postman`, obteniendo en una sola colección la gestión directa hacia `RabbitMQ` y el control de su `APIRest`.
