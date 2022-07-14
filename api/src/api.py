import os
import uuid
import configparser
import pymongo
import json
from typing import List, Optional
from fastapi import FastAPI
import requests
from pydantic import BaseModel, ValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "config.ini"))
MONGO_DB_URI = "mongodb+srv://admin:%s" % config['content database']['ATLAS_ADMIN']
API_URL_PREFIX = "/api/v0"

app = FastAPI(  openapi_url ="/api/lbl-mlexchange/openapi.json",
                docs_url    ="/api/lbl-mlexchange/docs",
                redoc_url   ="/api/lbl-mlexchange/redoc",
             )

#connecting to mongoDB Atlas
def conn_mongodb(collection='models'):
    client = pymongo.MongoClient(MONGO_DB_URI, serverSelectionTimeoutMS=100000)
    db = client['lbl-mlexchange']
    return db[collection]


@app.get(API_URL_PREFIX+"/import/datapath", tags=['datapath'])
def get_import_datapath():
    mycollection = conn_mongodb('datapath')
    return mycollection.find_one({"content_id": 1})
    
@app.get(API_URL_PREFIX+"/export/datapath", tags=['datapath'])
def get_export_datapath():
    mycollection = conn_mongodb('datapath')
    return mycollection.find_one({"content_id": 2})

@app.post(API_URL_PREFIX+"/import/datapath", tags=['datapath'])
def add_import_datapath(paths: list, key: str):
    mycollection = conn_mongodb('datapath')
    mycollection.update_one({
                              '_id': 1
                            },{
                              '$set': {
                              key: paths
                              }
                            }, upsert=False)
    return paths

@app.post(API_URL_PREFIX+"/export/datapath", tags=['datapath'])
def add_export_datapath(paths: list, key: str):
    mycollection = conn_mongodb('datapath')
    mycollection.update_one({
                              '_id': 2
                            },{
                              '$set': {
                              key: paths
                              }
                            }, upsert=False)
    return paths

