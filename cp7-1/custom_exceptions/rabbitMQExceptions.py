class RabbitMQError(Exception):
    def __init__(self, mensaje):
        super().__init__(mensaje)