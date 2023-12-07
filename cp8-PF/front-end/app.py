import json
from fastapi import FastAPI, Request, Response,Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import jwt
import os
import dotenv   

app = FastAPI()

dotenv.load_dotenv()
url_base = os.getenv("API_URL")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/",response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/login")
async def login(username: str, password: str, response: Response):
    async with httpx.AsyncClient() as client:
        r = await client.post(f'{url_base}/token', params={'username': username, 'password': password})
    #print(r.json())
    data = r.json()
    token = data['access_token']
    response.set_cookie(key="token", value=token, secure=False)  # Almacena el token en las cookies
    return JSONResponse(content=data)

@app.post("/enviar_para_analisis")
async def enviar_para_analisis(request: Request, message: str = Body(...)):    
    token = request.headers.get('Authorization')  # Recupera el token de las cabeceras
    if not token:
        return JSONResponse(content={'message': 'No token'})
    headers = {'Authorization': token}
    decoded_token = jwt.decode(token.split(' ')[1], options={"verify_signature": False})
    user = decoded_token['sub']
    message = json.loads(message)
    async with httpx.AsyncClient() as client:
        r = await client.post(f'{url_base}/publicar_mensaje_solicitud',
                              json={'message': message}, headers=headers)
    if r.content:
        try:
            data = r.json()
            print("post del front-end_enviando:",data)
            id_sol = data.get('id')
            response = JSONResponse(content=data)
            response.set_cookie(key="id_solicitud", value=id_sol, secure=False)  # Almacena el token en las cookies
            return response
        except:
            return JSONResponse(content={'message': 'No response body'})
    else:
        return JSONResponse(content={'message': 'No response body'})

@app.get("/recibir_resultado_final_analisis/{id_request}")
async def recibir_resultado_final_analisis(request: Request, id_request: str):
    token = request.headers.get('Authorization')  # Recupera el token de las cabeceras
    #print(f"recibiendo:{token}")
    if not token:
        return JSONResponse(content={'message': 'No token'})
    headers = {'Authorization': token}
    async with httpx.AsyncClient() as client:
        r = await client.get(f'{url_base}/consumir_mensaje_respuesta/{id_request}', headers=headers)
    if r.content:
        try:
            data = r.json()
            print("get del front-end_recibiendo:",data)
            id_sol = data.get('id')
            if id_request == id_sol:
                print("son iguales")
            else:
                print("son diferentes")
            return JSONResponse(content=data)
        except:
            return JSONResponse(content={'message': 'No response body'})
    else:
        return JSONResponse(content={'message': 'No response body'})
    
@app.get("/recibir_mensaje_para_analisis/{id_request}")  
async def recibir_mensaje_para_analisis(request: Request, id_request: str):
    token = request.headers.get('Authorization')  
    if not token:
        return JSONResponse(content={'message': 'No token'})
    headers = {'Authorization': token}
    async with httpx.AsyncClient() as client:
        r = await client.get(f'{url_base}/consumir_mensaje_solicitud/{id_request}', headers=headers)
    if r.content:
        try:
            data = r.json()
            print("get del front-end_recibiendo_analista:",data)
            id_sol = data.get('id')
            response = JSONResponse(content=data)
            return response
        except:
            return JSONResponse(content={'message': 'No response body'})
    else:
        return JSONResponse(content={'message': 'No response body'})

@app.post("/enviar_resultado_del_analisis/{id_request}")
async def enviar_resultado_del_analisis(request: Request, message: str = Body(...)):    
    token = request.headers.get('Authorization')
    if not token:
        return JSONResponse(content={'message': 'No token'})
    headers = {'Authorization': token}
    decoded_token = jwt.decode(token.split(' ')[1], options={"verify_signature": False})
    message = json.loads(message)
    id_request = request.cookies.get('id_solicitud')
    async with httpx.AsyncClient() as client:
        r = await client.post(f'{url_base}/publicar_mensaje_respuesta/{id_request}',
                              json={'message':message}, headers=headers)
    if r.content:
        try:
            data = r.json()
            id_sol = data.get('id')
            response = JSONResponse(content=data)
            if id_request == id_sol:
                print("son iguales")
            else:
                print("son diferentes")
            print("post del front-end_enviando:",data)
            return response
        except:
            return JSONResponse(content={'message': 'No response body'})
    else:
        return JSONResponse(content={'message': 'No response body'})
    
        


if __name__ == "__main__":
    import uvicorn
    dotenv.load_dotenv()
    ip_host = os.getenv("IP_HOST")
    uvicorn.run(app, host=ip_host, port=8000)