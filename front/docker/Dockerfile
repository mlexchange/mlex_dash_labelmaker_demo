FROM python:3.8-slim-buster as builder
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


COPY docker/requirements.txt requirements.txt

RUN pip3 install --upgrade pip &&\
    pip3 install -r requirements.txt 

FROM python:3.8-slim as build-image
COPY --from=builder /opt/venv /opt/venv


ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app/work
ENV HOME /app/work
ENV PYTHONUNBUFFERED=1
RUN useradd aasgreen
USER aasgreen
CMD ["/bin/bash"]
