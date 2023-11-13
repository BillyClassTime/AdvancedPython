#pip install aio_pika
import asyncio
import aio_pika

async def publish_message(channel, queue_name, message):
    await channel.default_exchange.publish(
        aio_pika.Message(body=message.encode()),
        routing_key=queue_name
    )
    print(f"Mensaje publicado: {message}")

async def consume_messages(channel, queue_name, stop_message="", task=None):
    # Declare a named queue with durable=True and auto_delete=False
    queue = await channel.declare_queue(queue_name, durable=True, auto_delete=False)

    # Purge the queue before consuming messages
    await queue.purge()

    async def on_message(message):
        nonlocal task
        body = message.body.decode()
        print(f"Mensaje consumido: {body}")

        if body == stop_message:
            print("Deteniendo el consumo de mensajes...")
            if task:
                task.cancel()

    consume_task = asyncio.create_task(queue.consume(on_message))

    try:
        await consume_task
    except asyncio.CancelledError:
        await queue.delete()

async def main():
    string_connection= "amqp://manager:su_clave@fqdn/"

    connection = await aio_pika.connect_robust(string_connection)

    channel = await connection.channel()

    queue_name = 'my_queue'
    stop_message = 'Salir'

    # Inicia la recepción de mensajes en un task separado
    receive_task = asyncio.create_task(
        consume_messages(channel, queue_name, stop_message))

    # Espera un momento antes de comenzar a enviar mensajes
    await asyncio.sleep(1)

    for i in range(3):
        await publish_message(channel, queue_name, f'Mensaje {i}')

    await publish_message(channel, queue_name, stop_message)

    # Espera a que termine la recepción de mensajes
    try:
        await receive_task
    except asyncio.CancelledError:
        pass

    # Cierra la conexión al finalizar
    await connection.close()

if __name__ == "__main__":
    asyncio.run(main())