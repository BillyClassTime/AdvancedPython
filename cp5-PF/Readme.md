# Pruebas Automatizadas en Postman

###  usuarioclave.json:

```json
[
	{"username":"Billy04","password":"P455w0rd1234"},
	{"username":"Billy05","password":"P455w0rd1234"},
	{"username":"Billy06","password":"P455w0rd1234"}
]
```

1.  Crear el entorno 

   ```
   Cree un entorno de pruebas o de desarrollo
   ```

2. No hace falta crear una variable token en la colección

3. Inicie la aplicación a probar

   ```
   cd cp4-PF
   Con el entorno Activo
   py main.py
   ```


## Casos de prueba

#### test failed login

```
curl -X POST --location 'http://localhost:8520/token' \
--header 'Accept: application/json' \
--header 'Content-Type: application/json' \
--data '{
  "username": "{{username}}",
  "password": "{{password}}"
}'
```

```json
Body:
{
  "username": "{{username}}",
  "password": "{{password}}"
}
```

```javascript
Test:
pm.test("Inicio de Sesión Fallido", function () {
  pm.response.to.have.status(401);
});
```

### test ok login

```
curl -X POST --location 'http://localhost:8520/token' \
--header 'Accept: application/json' \
--header 'Content-Type: application/json' \
--data '{
  "username": "{{username}}",
  "password": "{{password}}"
}'
```

```
Body:
{
  "username": "{{username}}",
  "password": "{{password}}"
}
```

```javascript
Test:
pm.test("Inicio de Sesión Exitoso", function () {
  pm.response.to.have.status(200);
  pm.response.to.have.jsonBody({ access_token: pm.response.json().access_token });

  // Almacenar el token para su uso posterior
  pm.environment.set("token", pm.response.json().access_token);
});

```

### test get client

```
curl -X GET --location 'http://localhost:8520/clientes' \
--header 'Authorization: Bearer e618f6127da5d4495b8ecd688ba39282' \
--data ''
```

```
Auth:
type 'Bearer Token' {{token}}
```

```javascript
Test:
pm.test("Obtener Clientes", function () {
    // Obtener el token del entorno
    let token = pm.environment.get("token");
    console.log(token);
    // Verificar que el token no sea nulo
    pm.expect(token).to.not.be.null;

    // Realizar la solicitud GET con el token en los encabezados
    pm.sendRequest({
        url: pm.variables.replaceIn("http://localhost:8520/clientes"),
        method: "GET",
        headers: {
            Authorization: `Bearer ${token}`
        }
    }, function(response)
    {
        pm.response.to.have.status(200);
    });
});
```

### test_max_failed_attempts

```
test login 3 veces
```

```javascript
Body:
{
  "username": "{{username}}",
  "password": "otra contraseña"
}
```

```javascript
Test:
pm.test("Inicio de Sesión Fallido", function () {
  pm.response.to.have.status(401);  
});
```

```
Cuenta bloqueda
```

```javascript
Body:
{
  "username": "{{username}}",
  "password": "otra contraseña"
}
```

```javascript
Test:
pm.test("Muchos Intentos Cuenta Bloqueada", function () {
  pm.response.to.have.status(429);  
});
```

