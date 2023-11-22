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

