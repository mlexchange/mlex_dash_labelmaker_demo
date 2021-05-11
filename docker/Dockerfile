#FROM tensorflow/tensorflow:latest-gpu
FROM python:3.8-slim-buster
#FROM nvcr.io/nvidia/tensorflow:20.03-tf2-py3
#FROM tensorflow/tensorflow:latest-gpu-py3
MAINTAINER ADAM GREEN

COPY requirements.txt requirements.txt

RUN apt-get update && apt-get install -y \
    build-essential \
    libhdf5-dev \
    wget \
    vim \
    python3-pip 

RUN pip3 install --upgrade pip &&\
    pip3 install -r requirements.txt 


WORKDIR /work
ENV HOME /work
ENV PYTHONUNBUFFERED=1

CMD ["/bin/bash"]
#CMD ["streamlit", "run", "ui.py"]
