import asyncio
from azure.servicebus.aio import ServiceBusClient
#NAMESPACE_CONNECTION_STR = "Endpoint=sb://[namepace].servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=[KEY]"
#QUEUE_NAME = "Queue name"

NAMESPACE_CONNECTION_STR = "Endpoint=sb://curso01python2023.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=/y8TMT8M9ilN58m7b3s7BFq5+t+78f8xY+ASbAH4r84="
QUEUE_NAME = "my-cola"

async def run():
    # create a Service Bus client using the connection string
    async with ServiceBusClient.from_connection_string(
        conn_str=NAMESPACE_CONNECTION_STR,
        logging_enable=True) as servicebus_client:

        async with servicebus_client:
            # get the Queue Receiver object for the queue
            receiver = servicebus_client.get_queue_receiver(queue_name=QUEUE_NAME)
            async with receiver:
                received_msgs = await receiver.receive_messages(max_wait_time=5, max_message_count=20)
                for msg in received_msgs:
                    print("Received: " + str(msg))
                    # complete the message so that the message is removed from the queue
                    await receiver.complete_message(msg)
asyncio.run(run())