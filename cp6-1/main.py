from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS
origins = [
    "http://localhost:8000",
    "http://localhost",
    "http://yourdomain.com",
    "https://your_frontend_domain.com",
    "http://your_frontend_domain.net",
    "http://192.168.88.49:8000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.middleware("http")
async def add_cors_header(request: Request, call_next):
    response = await call_next(request)
    request_origin = request.headers.get('Origin')
    print(request_origin)
    if request_origin in origins:
        response.headers['Access-Control-Allow-Origin'] = request_origin

    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    return response
#Rutas de ejemplo
@app.get("/")
def read_root():
    return {"message": "Respuesta desde el servidor"}

@app.get("/data")
def read_data():
    data={"example_data": "Respuesta con datos desde el servidor"}
    return data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.88.50", port=8000)