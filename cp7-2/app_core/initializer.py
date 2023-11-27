from api.routes import rabbitMQRoutes
from api.routes import securityRoutes
from fastapi import FastAPI, HTTPException
from custom_exceptions.customExceptions import customException
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

app.include_router(rabbitMQRoutes.route)
app.include_router(securityRoutes.router)