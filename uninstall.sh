#!/bin/bash

docker-compose -f docker-compose-master-local.yml down
docker container prune
