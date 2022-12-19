import os
import uuid
import configparser
import pymongo
import json
from typing import List, Optional
from fastapi import FastAPI
import requests
from uuid import uuid4

from pydantic import BaseModel, ValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from model import Dataset, OperationType


MONGO_DB_USERNAME = str(os.environ['MONGO_INITDB_ROOT_USERNAME'])
MONGO_DB_PASSWORD = str(os.environ['MONGO_INITDB_ROOT_PASSWORD'])
MONGO_DB_URI = "mongodb://%s:%s@mongodb:27017/?authSource=admin" % (MONGO_DB_USERNAME, MONGO_DB_PASSWORD)
API_URL_PREFIX = "/api/v0"

client = pymongo.MongoClient(MONGO_DB_URI)
db = client['labelmaker']
mycollection = db['datapath']


app = FastAPI(openapi_url ="/api/labelmaker/openapi.json",
              docs_url    ="/api/labelmaker/docs",
              redoc_url   ="/api/labelmaker/redoc",
             )


@app.get(API_URL_PREFIX+"/datapath/{operation_type}", tags=['datapath'])
def get_datapath(operation_type: OperationType, user_id: str = None):
  subqueries = [{'operation_type': operation_type}]
  if user_id:
      subqueries.append({"user_id": user_id}) 
  query = {"$and": subqueries}
  return mycollection.find_one(query, {'_id': 0})


@app.post(API_URL_PREFIX+"/datapath", tags=['datapath'])
def add_datapath(dataset: Dataset):
  # check if dataset exists
  current_dataset = mycollection.find_one({'user_id': dataset.user_id, 'operation_type': dataset.operation_type})
  if current_dataset:
    dataset.uid = current_dataset['uid']
    dataset_dict = dataset.dict()
    mycollection.update_one({'uid': current_dataset['uid']}, {'$set': dataset_dict}, upsert=False)
  else:
    dataset.uid = str(uuid4())
    dataset_dict = dataset.dict()
    mycollection.insert_one(dataset_dict)
  return dataset.uid
