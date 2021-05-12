#FROM tensorflow/tensorflow:latest-gpu
FROM python:3.8-slim-buster as builder
#FROM nvcr.io/nvidia/tensorflow:20.03-tf2-py3
#FROM tensorflow/tensorflow:latest-gpu-py3
MAINTAINER ADAM GREEN


RUN apt-get update && apt-get install -y \
    build-essential \
    libhdf5-dev \
    wget \
    vim \
    python3-pip 

# virtual env for builder pattern
RUN python -m venv /opt/venv \ 
    && pip3 install --upgrade pip
ENV PATH="/opt/venv/bin:$PATH"

# add all dependencies individually during dev, to take advantage of
# caching.
RUN pip3 install h5py==2.10.0
RUN pip3 install scipy
RUN pip3 install pillow
RUN pip3 install dash
RUN pip3 install dash-bootstrap-components
RUN pip3 install numpy
RUN pip3 install config
RUN pip3 install matplotlib
RUN pip3 install aiohttp
RUN pip3 install sseclient
RUN pip3 install altair
RUN pip3 install flask
RUN pip3 install Flask-Caching


#COPY requirements.txt requirements.txt
FROM python:3.8-slim as build-image
COPY --from=builder /opt/venv /opt/venv


ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /work
ENV HOME /work
ENV PYTHONUNBUFFERED=1
RUN useradd aasgreen
USER aasgreen
CMD ["/bin/bash"]
#CMD ["streamlit", "run", "ui.py"]
