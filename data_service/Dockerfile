from ubuntu:20.04
MAINTAINER ADAM GREEN



RUN apt-get update && apt-get install -y python3-pip\
    python3 \
    git
RUN pip3 install --upgrade pip
RUN pip3 install dvc
RUN pip3 install dvc[gdrive]
WORKDIR /working
#RUN useradd aasgreen
#USER aasgreen

ENV PYTHONUNBUFFERED=1
CMD ["sleep", "6000"]
