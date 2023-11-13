#conexión a RabbitMQ
import pika
usuario = "admin"
clave = "admin2017"
credenciales = pika.PlainCredentials(usuario, clave)
parametros = pika.ConnectionParameters('localhost', 5672, 
                                       '/', credenciales)
conexion = pika.BlockingConnection(parametros)
channel = conexion.channel()

#Publicar un mensaje(producer)
print("Productor")
channel.basic_publish(exchange='', routing_key='cola1', 
                      body='Mensaje Inicial')
print("Enviamos el mensaje inicial")
channel.basic_publish(exchange='', routing_key='cola1', 
                      body='Salir')
print("Enviamos el mensaje de salida")
print("Salir")
print("-"*20)

#Consumir un mensaje(consumer)
print("Consumidor")
channel.queue_declare(queue='cola1')
def callback(ch, method, properties, body):
    print("Mensaje recibido %r" % body.decode('utf-8'))
    if body == b'Salir':
        print("Cerrando conexión")
        channel.stop_consuming()
channel.basic_consume(queue='cola1', 
                      on_message_callback=callback, auto_ack=True)
print('Esperando mensajes...')
channel.start_consuming()

#Cerrar la conexión
channel.close()
conexion.close()