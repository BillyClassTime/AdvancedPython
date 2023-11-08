from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from starlette.responses import PlainTextResponse
import json

app = FastAPI()

class Tarea(BaseModel):
    nombre: str
    completada: bool
    links: dict = {}

def load_tareas():
    try:
        with open("tareas.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_tareas(tareas):
    with open("tareas.json", "w") as f:
        json.dump(tareas, f, indent=2)

@app.get("/tareas", response_model=list[Tarea])
def obtener_tareas():
    tareas = load_tareas()
    for i, tarea in enumerate(tareas):
        tarea['links'] = {
            "self": f"http://dominiox:8090/tareas/{i}",
            "delete": f"http://dominiox:8090/tareas/{i}"
        }
    return PlainTextResponse(json.dumps(tareas), status_code=200)

@app.get("/tareas/{tarea_id}", response_model=Tarea)
def obtener_tarea(tarea_id: int):
    tareas = load_tareas()
    if tarea_id >= len(tareas):
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    tarea = tareas[tarea_id]
    tarea['links'] = {
        "self": f"http://localhost:8090/tareas/{tarea_id}",
        "delete": f"http://localhost:8090/tareas/{tarea_id}"
    }
    return PlainTextResponse(json.dumps(tarea), status_code=200)

@app.post("/tareas", response_model=Tarea)
def crear_tarea(tarea: Tarea):
    tareas = load_tareas()
    tarea_dict = json.loads(tarea.model_dump_json())
    tarea_dict['links'] = {
        "self": f"http://localhost:8090/tareas/{len(tareas)}",
        "delete": f"http://localhost:8090/tareas/{len(tareas)}"
    }
    tareas.append(tarea_dict)
    save_tareas(tareas)
    return PlainTextResponse("Tarea creada", status_code=201)

@app.put("/tareas/{tarea_id}", response_model=Tarea)
def update_tarea(tarea_id:int, tarea: Tarea):
    tareas = load_tareas()
    if tarea_id >= len(tareas):
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    tarea_dict = json.loads(tarea.model_dump_json())
    tarea_dict['links'] = {
        "self": f"http://localhost:8090/tareas/{tarea_id}",
        "delete": f"http://localhost:8090/tareas/{tarea_id}"
    }
    tareas[tarea_id] = tarea_dict
    save_tareas(tareas)
    return PlainTextResponse(json.dumps(tareas), status_code=200)
    #return tareas

@app.delete("/tareas/{tarea_id}")
def delete_tarea(tarea_id:int):
    tareas = load_tareas()
    if tarea_id >= len(tareas):
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    del tareas[tarea_id]
    save_tareas(tareas)
    return PlainTextResponse("Tarea eliminada", status_code=200)

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)
 
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)