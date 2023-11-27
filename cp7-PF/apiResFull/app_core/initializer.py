from api.routes import rabbitMQRoutes
from api.routes import securityRoutes
from fastapi import FastAPI, HTTPException
from custom_exceptions.customExceptions import customException
from fastapi.middleware.cors import CORSMiddleware
import logging

app = FastAPI()

logging.basicConfig(filename='logs.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)

@app.exception_handler(HTTPException)
async def exception_handler(request, exc: HTTPException):
    logger.error(f"{exc.detail}")
    error_message = f"{exc.detail}"
    raise HTTPException(status_code=500,detail=error_message)

@app.exception_handler(customException)
async def exception_handler(request, exc: customException):
    logger.error(f"{exc.detail}")
    error_message = f"{exc.detail}"
    raise HTTPException(status_code=500,detail=error_message)

origins = [
    "http://localhost:15000",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET","POST","PUT","DELETE"],
    allow_headers=["*"],
)

app.include_router(rabbitMQRoutes.route)
app.include_router(securityRoutes.router)