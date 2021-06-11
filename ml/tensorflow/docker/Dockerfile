FROM tensorflow/tensorflow:latest-gpu
#FROM nvcr.io/nvidia/tensorflow:20.03-tf2-py3
#FROM tensorflow/tensorflow:latest-gpu-py3
MAINTAINER ADAM GREEN

COPY requirements.txt requirements.txt

RUN apt-get update && apt-get install -y \
    build-essential \
    libhdf5-dev \
    wget \
    python3-pip\
    graphviz

RUN pip3 install --upgrade pip &&\
    pip3 install -r requirements.txt 

#CMD ["bash","call_defect.sh"]
#EXPOSE 8501

ENV PYTHONUNBUFFERED=1
WORKDIR /work
ENV HOME /work

COPY Train.py Train.py
COPY ml_label_maker.py ml_label_maker.py

CMD ["/bin/bash"]

