FROM python:3.9
MAINTAINER THE MLEXCHANGE TEAM

RUN ls
COPY requirements.txt requirements.txt

RUN pip3 install --upgrade pip &&\
    pip3 install -r requirements.txt\
    pip install git+https://github.com/mlexchange/mlex_file_manager

WORKDIR /app/work
ENV HOME /app/work
ENV PYTHONPATH "${PYTHONPATH}:/app/work"
COPY src src

CMD ["bash"]
CMD python3 src/labelmaker.py
