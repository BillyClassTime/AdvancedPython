from fastapi import FastAPI, Request, Response
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

@app.post("/sendmessage/{message}")
async def sendmessage(request: Request, message: str):
    token = request.headers.get('Authorization')  # Recupera el token de las cabeceras
    #print(f"enviando:{token}")
    if not token:
        return JSONResponse(content={'message': 'No token'})
    headers = {'Authorization': token}
    decoded_token = jwt.decode(token.split(' ')[1], options={"verify_signature": False})
    user = decoded_token['sub']
    message = f"{user}: {message}"
    async with httpx.AsyncClient() as client:
        r = await client.post(f'{url_base}/publicar/{message}', headers=headers)
    if r.content:
        try:
            data = r.json()
            return JSONResponse(content=data)
        except:
            return JSONResponse(content={'message': 'No response body'})
    else:
        return JSONResponse(content={'message': 'No response body'})
    
@app.get("/receivemessage")
async def receivemessage(request: Request):
    token = request.headers.get('Authorization')  # Recupera el token de las cabeceras
    #print(f"recibiendo:{token}")
    if not token:
        return JSONResponse(content={'message': 'No token'})
    headers = {'Authorization': token}
    async with httpx.AsyncClient() as client:
        r = await client.get(f'{url_base}/consumir', headers=headers)
    if r.content:
        try:
            data = r.json()
            print(data)
            return JSONResponse(content=data)
        except:
            return JSONResponse(content={'message': 'No response body'})
    else:
        return JSONResponse(content={'message': 'No response body'})    

if __name__ == "__main__":
    import uvicorn
    dotenv.load_dotenv()
    ip_host = os.getenv("IP_HOST")
    uvicorn.run(app, host=ip_host, port=8000)