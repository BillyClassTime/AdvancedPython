import json
import base64
import uuid


import uuid

def is_valid_uuid(id_request):
    try:
        uuid.UUID(id_request)
        return True
    except ValueError:
        return False

def messageToBase64(message):
    data_str = json.dumps(message)
    encoded_data = base64.b64encode(data_str.encode("utf-8")).decode("utf-8")
    return encoded_data

def base64ToMessage(encoded_message):
    decoded_data = base64.b64decode(encoded_message).decode("utf-8")
    message = json.loads(decoded_data)
    return message

def conform_message_request(message):
    request_message = {
        "id": "",
        "kind": "analysis_request",
        "mensaje": message
    }
    mensaje_id = str(uuid.uuid4())
    request_message['id'] = mensaje_id
    encoded_message = messageToBase64(message)
    request_message['mensaje'] = encoded_message
    return request_message

def conform_message_response(id, message):
    response_message = {
        "id": "",
        "kind": "analysis_response",
        "mensaje": message
    }
    response_message['id'] = id
    encoded_message = messageToBase64(message)
    response_message['mensaje'] = encoded_message
    return response_message

if __name__ == "__main__":
    message = {
        "nombre": "Juan",
        "edad": 30,
        "ciudad": "Madrid"
    }
    request_message = conform_message_request(message)
    message = {
        "analisis_mensaje": "Nombre: Juan, Edad: 30, Ciudad: Madrid",
        "fecha_análisis": "2021-05-01 12:00:00",
        "analista": "Analista 1",
        "resultado": "Nombres de personas: 1, Nombres de ciudades: 1, Edades: 1"
    }
    response_message = conform_message_response(request_message['id'], message)
    print(f"JSON de solicitud: {request_message}")
    print(f"JSON de respuesta: {response_message}")
