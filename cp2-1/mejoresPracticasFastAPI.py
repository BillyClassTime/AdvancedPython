from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.responses import PlainTextResponse

app = FastAPI()

class Elemento(BaseModel):
    id: int
    nombre: str

def get_elemento_from_list(id: int, elementos: list):
    try:
        return next(e for e in elementos if e.id == id)
    except StopIteration:
        return None

@app.get("/api/elementos/{id}", response_model=Elemento)
def get_elemento(id: int):
    elementos = [ Elemento(id=1, nombre="elemento1"), 
                 Elemento(id=2, nombre="elemento2"), 
                 Elemento(id=3, nombre="elemento3") ]
    elemento = get_elemento_from_list(id, elementos)

    if elemento is None:
        raise HTTPException(status_code=404, detail="Elemento no encontrado")

    return elemento

@app.get("/api/elementos", response_model=list[Elemento])
def get_elementos():
    elementos = [
        Elemento(id=1, nombre="elemento1"),
        Elemento(id=2, nombre="elemento2"),
        Elemento(id=3, nombre="elemento3")
    ]

    return elementos

@app.get("/api/error/400")
def error_400():
    raise HTTPException(status_code=400, detail="Bad Request")

@app.get("/api/error/403")
def error_403():
    raise HTTPException(status_code=403, detail="Forbidden")

@app.get("/api/error/404")
def error_404():
    raise HTTPException(status_code=404, detail="Not Found")

@app.get("/api/error/500")
def error_500():
    raise HTTPException(status_code=500, detail="Internal Server Error")

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)