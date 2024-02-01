#!/bin/bash

docker pull ghcr.io/mlexchange/mlex_image_classification:main
docker pull ghcr.io/mlexchange/mlex_pytorch_autoencoders:main
docker-compose up -d
