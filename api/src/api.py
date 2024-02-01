import logging
import os
from fastapi import FastAPI
from pymongo import MongoClient

from src.model import Dataset
from src.data_service import DataService

logger = logging.getLogger('splash_ml')

def init_logging():
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)

MONGO_DB_USERNAME = str(os.environ.get('MONGO_INITDB_ROOT_USERNAME', default=""))
MONGO_DB_PASSWORD = str(os.environ.get('MONGO_INITDB_ROOT_PASSWORD', default=""))
MONGO_DB_URI = "mongodb://%s:%s@mongodb:27017/?authSource=admin" % \
               (MONGO_DB_USERNAME, MONGO_DB_PASSWORD)
API_URL_PREFIX = "/api/v0"

init_logging()

app = FastAPI(openapi_url ="/api/labelmaker/openapi.json",
              docs_url    ="/api/labelmaker/docs",
              redoc_url   ="/api/labelmaker/redoc")

def set_data_service(new_data_svc: DataService):
    global data_svc
    data_svc = new_data_svc

@app.on_event("startup")
async def startup_event():
    logger.debug('!!!!!!!!!starting server')
    db = MongoClient(MONGO_DB_URI)
    set_data_service(DataService(db))


@app.get(API_URL_PREFIX+"/dataset", tags=['datapath'])
def get_dataset(user_id: str = None) -> Dataset:
  dataset = data_svc.get_dataset(user_id)
  return dataset


@app.post(API_URL_PREFIX+"/dataset", tags=['datapath'])
def add_dataset(dataset: Dataset) -> str:
  uid = data_svc.add_dataset(dataset)
  return uid

