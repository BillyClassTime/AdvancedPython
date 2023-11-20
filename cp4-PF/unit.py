import unittest
from fastapi.testclient import TestClient
from mitigarFuerzaBruta import app,token_store, failed_login_store

class TestLogin(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        # Restablecer el estado después de cada prueba
        token_store.clear()
        failed_login_store.clear()

    def test_failed_login(self):
        response = self.client.post("/token", json={"username": "user", "password": "wrong_password"})
        self.assertEqual(response.status_code, 401)
        self.assertIn("Credenciales incorrectas", response.json()["detail"])

    def test_successful_login(self):
        # Primero, intentar iniciar sesión con una contraseña incorrecta
        response = self.client.post("/token", json={"username": "user", "password": "wrong_password"})
        self.assertEqual(response.status_code, 401)

        # Luego, intentar iniciar sesión de nuevo con la misma contraseña
        response = self.client.post("/token", json={"username": "user", "password": "wrong_password"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())
        self.assertEqual(failed_login_store.get("user", {}).get("attempts", 0), 0)

    def test_get_clients(self):
        # Primero, intentar iniciar sesión con una contraseña incorrecta
        response = self.client.post("/token", json={"username": "user", "password": "wrong_password"})
        self.assertEqual(response.status_code, 401)

        # Luego, intentar iniciar sesión de nuevo con la misma contraseña
        response = self.client.post("/token", json={"username": "user", "password": "wrong_password"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())
        token = response.json()["access_token"]

        # Ahora, usar el token para obtener la lista de clientes
        response = self.client.get("/clientes", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Lista de clientes"})

    def test_max_failed_attempts(self):
        for i in range(3):
            print(f"intentando {i+1}...")
            response = self.client.post("/token", json={"username": "userA", "password": f"wrong_password{i}"})
            self.assertEqual(response.status_code, 401)

        # Ahora, después de 3 intentos fallidos, el cuarto intento debería ser bloqueado
        print("intentando 3...")
        response = self.client.post("/token", json={"username": "userA", "password": "wrong_password3"})
        self.assertEqual(response.status_code, 429)
        self.assertIn("Demasiados intentos fallidos. Por favor, inténtalo más tarde.", response.json()["detail"])

if __name__ == '__main__':
    unittest.main()