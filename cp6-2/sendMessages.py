import asyncio
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage

NAMESPACE_CONNECTION_STR = "Endpoint=sb://curso01python2023.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=/y8TMT8M9ilN58m7b3s7BFq5+t+78f8xY+ASbAH4r84="
QUEUE_NAME = "my-cola"

async def send_single_message(sender):
    # Create a Service Bus message and send it to the queue
    message = ServiceBusMessage("Single Message")
    await sender.send_messages(message)
    print("Sent a single message")

async def run():
    # create a Service Bus client using the connection string
    async with ServiceBusClient.from_connection_string(
        conn_str=NAMESPACE_CONNECTION_STR,
        logging_enable=True) as servicebus_client:
        # Get a Queue Sender object to send messages to the queue
        sender = servicebus_client.get_queue_sender(queue_name=QUEUE_NAME)
        async with sender:
            # Send one message
            await send_single_message(sender)
            # Send a list of messages
            #await send_a_list_of_messages(sender)
            # Send a batch of messages
            #await send_batch_message(sender)    

asyncio.run(run())
print("Done sending messages")