# Práctica Final del Dia

### API Rest en FastAPI con Seguridad Avanzada

Implementar

- [ ] Autenticación y Tokens

  Utilizar el esquema OAuth2 para la autenticación mediante la recuperación del token en el endpoint `/token`

  Proporcionar las credenciales (usuario y contraseña) las cuales hay que verificcar y si son validas emitir un token de acceso

  Llevar un registro de intentos fallidos de inicio de sesión para mitigar las amenazas de ataques de diccionario y de fuerza bruta

- [ ] Rutas Protegidas

  - [ ] Crear la ruta `/clientes`que requerirá autenticación para acceder
  - [ ] La ruta por solicitud GET devolverá una lista de clientes simulada

- [ ] Distribución de Carpetas

  - [ ] Cumplir con los estandares de configuración de proyecto

    - [ ]  carpeta `api\routes`, contendrá las rutas especificas de la aplicación `login.py` organizarlas utilizando el enrutador `APIRouter`

    - [ ]    carpeta `app`,contendrá el archivo principal `main.py` que crea la instancia de FastAPI y agrega los enrutadores definidos en `api/routes`

    - [ ]    `core`, contendrá el módulo `security.py`con las funciones relacionadas con la seguridad, como el hash de contraseñas y la validación de tokens

    - [ ]    `test`, contendrá las pruebas unitarias relacionadas con el código

- [ ] Estandares de Seguridad

    - [ ] Utilizar OAuth2 para la autenticación

    - [ ] Utilizar un generador de token de acceso simple utilizando `secrets.token.hex(16)` simulando un token JWT

      > En prácticas futuras se generará el token con `PyJWT` para generar tokens que contengan información codificada en formato JSON y firmados digitalmente para asegurar su integridad

    - [ ] Gestionar los intentos fallidos de inicio de session y bloquear durante un tiempo, después de un cierto número de intentos

- [ ] Mantenibilidad y Escalabilidad

    - [ ] Organizar el código en módulos y carpetas separadas para mejorar la mantenibilidad

    - [ ] Utilizar un enfoque modular con FastAPI y `APIRouter`para separar la lógica de la ruta

    - [ ] Agrupar en el módulo `core`las funciones esenciales relacionadas con la seguridad para facilitar la gestión

        
    
    ### Pruebas con scripts de powershell
    
    ```powershell
    .\test_api.ps1 -usuario billy -clave <su_clave>
    ```
    
    ```powershell
    Error al realizar la solicitud: {"detail":"Credenciales incorrectas"}
    ```
    
    ```powershell
    .\test_api_token.ps1 -token <token>
    ```
    
    

 