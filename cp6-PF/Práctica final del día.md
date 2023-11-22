# Práctica final del día

### Configuración de una conexión y envío de mensajes desde una aplicación FastAPI a Azure Service Bus.

1. Estructura del proyecto

   ```
   My Proyect:
   ├───api
   │   └───routes
   │            └─── __init__.py
   |                 serviceBusRoute.py
   ├───app_core
   │   └───__init__.py
   │       initializer.py
   ├───services
   │   └───__init__.py
   │       azureServiceBus.py
   ├───env
   │       #Python 3.9.10
   └───test
   │   └───__init__.py
   │       unit_integration.py
   main.py
   requeriment.txt
   ```

2. Librerias y entorno

   ``` powershell
   py -m pip install --upgrade pip
   pip install fastapi azure-servicebus uvicorn
   ```

3. Servicios

   ```python
   import asyncio
   from azure.servicebus.aio import ServiceBusClient
   from azure.servicebus import ServiceBusMessage
   ```

   Importar las librerias necesiarias.

   La biblioteca `asyncio` se importa en este código porque se utiliza para manejar la asincronía en las operaciones de Azure Service Bus.

   La biblioteca `azure.servicebus.aio` es una versión asincrónica de la biblioteca `azure.servicebus`. Esta versión asincrónica utiliza `asyncio` para manejar las operaciones de E/S de manera asincrónica, lo que puede mejorar el rendimiento al permitir que otras tareas se ejecuten mientras se espera la respuesta de Azure Service Bus.

   - Creación de la clase gestora de servicios

   ```python
   class azureServicesBus():
       def __init__(self): # Utilizado para gestión de la cadena de conexión 
       #Utilizado para la conexión y autenticación con service bus
       	pass
   
   	async def enviar_mensaje_a_cola(self, mensaje_content, cola_nombre): 
           pass
   
       async def recibir_mensaje_de_cola(self, cola_nombre):
           pass
   ```

   ```python
   def __init__(self):    
       self.connectionString="Cadena_de Conexión"
       self.client = ServiceBusClient.from_connection_string(
           conn_str=self.connectionString,
           logging_enable=True)
   ```

   ```python
   async def enviar_mensaje_a_cola(self, mensaje_content, cola_nombre):
       try:
           sender = self.client.get_queue_sender(queue_name=cola_nombre)
           async with sender:
               message = ServiceBusMessage(mensaje_content)
               await sender.send_messages(message)
               return {"status": "Sent a single message"}
       except Exception as e:
           print(str(e))
   ```

   ```  python
   async def recibir_mensaje_de_cola(self, cola_nombre):
       try:
           receiver = self.client.get_queue_receiver(queue_name=cola_nombre)
           async with receiver:
               messages = await receiver.receive_messages(max_message_count=1,
                                                          max_wait_time=5)
               if messages:
                   # Decode the bytes to a string
                   message_body = "".join(b.decode('utf-8') for b in messages[0].body)
                   # Complete the message to remove it from the queue
                   await receiver.complete_message(messages[0])
                   return {"message": message_body}
               else:
                   return {"message": "No hay mensajes"}    
       except Exception as e:
           print(str(e))
   ```

   Salve el fichero como azureServiceBus.py

4. Rutas

   En la carpeta `api\routes` definimos el código para involucrar los servicios con nuestras rutas

   - Importamos librerías

     ```python
     from fastapi import APIRouter, HTTPException
     from services.azureServicesBus import azureServicesBus
     ```

   - Inicializamos la gestión de rutas

     ```python
     route = APIRouter()
     ```

   - Definimos la ruta de envío

     ```python
     @route.post("/enviar-mensaje/{cola_nombre}")
     async def enviar_mensaje(cola_nombre: str, mensaje: str):
         try:
             asb = azureServicesBus()
             return await asb.enviar_mensaje_a_cola(mensaje, cola_nombre)    
         except Exception as e:
             raise HTTPException(status_code=500, detail=str(e))

   - Definimos la ruta de recepción

     ```python
     @route.get("/recibir-mensaje/{cola_nombre}")
     async def recibir_mensaje(cola_nombre: str):
         try:
             asb= azureServicesBus()
             return await asb.recibir_mensaje_de_cola(cola_nombre)
         except Exception as e:
             raise HTTPException(status_code=500, detail=str(e))
     ```

   Salva este fichero como `serviceBusRoutes.py`

4. Carpeta de aplicación y core del proyecto

   Librerías y dependencias:

   ```python
   from fastapi import FastAPI
   from api.routes import serviceBusRoutes as azureservice
   ```

   Inicialización e instanciación

   ```python
   app = FastAPI()
   app.include_router(azureservice.route)
   ```

   Salva este fichero como `initializer.py`

5. Punto de entrada principal de la aplicación

   Librerías y dependencias

   ```python
   from app_core.initializer import app
   ```

   Punto de entrada principal

   ```python
   if __name__ == "__main__":
       import uvicorn
       uvicorn.run(app, host="0.0.0.0", port=9080)
   ```

6. Pruebas de integración

   - Pruebas de integración

     ```python
     import unittest, asyncio
     from services.azureServicesBus import azureServicesBus
     
     class TestAzureServicesBusIntegration(unittest.TestCase):
         def setUp(self):
             self.asb = azureServicesBus()
     
         def test_enviar_mensaje(self):
             # Enviar un mensaje
             result_envio = asyncio.run(self.asb.enviar_mensaje_a_cola("test message", "my-cola"))
             self.assertEqual(result_envio, {"status": "Sent a single message"})
     
         def test_recibir_mensaje(self):
             # Recibir el mensaje
             result_recepcion = asyncio.run(self.asb.recibir_mensaje_de_cola("my-cola"))
             self.assertEqual(result_recepcion, {"message": "test message"})
     
     if __name__ == '__main__':
         unittest.main()
     
     if __name__ == '__main__':
         unittest.main()
     ```

     Salvar a este fichero `unit_integration.py`

     Ejecutar la pruebas de integración `py -m unittest test/unit_integration`

   