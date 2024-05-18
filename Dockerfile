FROM python:3.11
MAINTAINER THE MLEXCHANGE TEAM

RUN ls
COPY pyproject.toml pyproject.toml
COPY README.md README.md

RUN pip3 install --upgrade pip &&\
    pip3 install . &&\
    pip install git+https://github.com/mlexchange/mlex_file_manager

WORKDIR /app/work
ENV HOME /app/work
ENV PYTHONPATH "${PYTHONPATH}:/app/work"
COPY src src
COPY labelmaker.py labelmaker.py
COPY gunicorn_config.py gunicorn_config.py

CMD ["bash"]
CMD gunicorn -c gunicorn_config.py --reload labelmaker:server
