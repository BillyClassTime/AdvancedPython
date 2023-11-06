# **Grupo 1: API de Tareas To-Do**

**Lenguaje de Programación:** Python

**Marco de Desarrollo:** Flask

**Editor de Código:** Visual Studio Code

**Sistema de Gestión de Datos:** PostgreSQL

**Objetivo:** Desarrollar una API que permita a los usuarios gestionar sus tareas pendientes (To-Do). Los usuarios pueden crear, leer, actualizar y eliminar tareas.

**Estructura de Rutas y Endpoints:**

- ```
  /tasks
  ```

   (Ruta base para las tareas)

  - `GET /tasks` (Recupera la lista de todas las tareas)

  - `POST /tasks` (Crea una nueva tarea)

  - ```
    /tasks/<task_id>
    ```

     (Ruta para una tarea específica)

    - `GET /tasks/<task_id>` (Recupera una tarea específica)
    - `PUT /tasks/<task_id>` (Actualiza una tarea específica)
    - `DELETE /tasks/<task_id>` (Elimina una tarea específica)

**Implementación de Rutas y Endpoints:**

- Utiliza Flask para definir las rutas y endpoints.
- Implementa funciones para cada uno de los endpoints, gestionando las operaciones CRUD (GET, POST, PUT, DELETE) y la interacción con la base de datos PostgreSQL.
- Asegúrate de manejar los parámetros de solicitud, como JSON para las solicitudes POST y PUT, y proporcionar respuestas claras, como JSON para las respuestas.

**Pruebas Unitarias:**

- Crea pruebas unitarias para cada una de las funciones de los endpoints.
- Asegúrate de que las pruebas cubran casos de éxito y errores, como tareas no encontradas, solicitudes incorrectas, etc.