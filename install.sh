#!/bin/bash

docker-compose -f docker-compose-models.yml pull
docker tag mlexchange1/unsupervised-classifier:1.0 mlexchange1/unsupervised-classifier:latest
docker tag mlexchange1/tensorflow-neural-networks:1.0 mlexchange1/tensorflow-neural-networks:latest

docker-compose -f docker-compose-master-local.yml up --build -d
