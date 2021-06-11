# Dash LabelMaker

Simple microservices application with a Dash UI, a rabbitmq job queue, and a compute_server

- compute_launcher is the rabbitmq consumer which launches the ml containers
- front is the front-end, written in dash-python
- ml is the tensorflow predefined ml models (cannibalized from Alex's streamlit code)

## Running
First, make sure that the ML image has been built:
```
cd ml/tensorflow
make build_docker
```
Then execute:
```
cd ../../
docker-compose up
docker-compose buil
```
## Outline of Project
docker-compose contains the build instructions for the docker containers

## compute_launcher
This contains the ml_worker.py (the ml_worker.sh is old, I haven't deleted it because
the knowledge contained within was hard won)

### Compute Launcher
```
.
├── compute_launcher
│   ├── Dockerfile
│   ├── ml_worker.py
│   ├── ml_worker.sh
│   ├── requirements.txt
├── data
├── docker-compose.yml
├── front
│   ├── docker
│   │   ├── app.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── __init__.py
│   ├── Makefile
│   ├── readme.md
│   └── src
│       ├── app.py
│       ├── apps
│       │   ├── templates.py
│       │   ├── thumbnail_tab.py
│       │   ├── training.py
│       │   └── welcome.py
│       ├── assets
│       │   ├── mlex.png
│       │   └── segmentation-style.css
│       ├── index.py
│       ├── mlex_api
│       │   ├── LICENSE
│       │   ├── mlex_api
│       │   │   ├── database_interface.py
│       │   │   ├── data_tooling.py
│       │   │   ├── __init__.py
│       │   │   ├── job_dispatcher.py
│       │   ├── README.md
│       │   └── setup.py
│       ├── output.csv
│       ├── tab_app.py
│       ├── templates.py
│       └── thumbnail.py
├── ml
│   └── tensorflow
│       ├── data
│       ├── Deploy.py
│       ├── docker
│       │   └── Dockerfile
│       ├── Makefile
│       ├── ml_label_maker.py
│       ├── requirements.txt
│       └── Train.py
└── README.md
```


# 2021-06-09
Just figured out that subprocess is blocking! This is annoying, I thought that it would be non-blocking (fork a process off), but I guess it makes sense-- python blocks until the sub process returns. I am going to use a multiprocessing.process to launch this. Hopefully it works.  
# 2021-06-08
The biggest priority is to make the ml_worker.py program threadsafe. It is currently missing the heartbeat, which causes the docker command to be un_acked, which means it doesn't go away from the queue, so it keeps executing.

There is a threadsafe pika implementation, but I also need to refactor the code in ml_worker, so it is more managable anyway. This will be an all day project, at least.

The message passing queue is still the most fragile. The recommended way to use the pika library is to have a long lived connection, and then pass that around. To do this, you need a robust connection handler/class, where if the connection crashes (all to frequently :) ) it can be gracefully re-connected. This is because it is slow to re-establish a connection.

Instead of this, I'm just opening and closing connections every time someone presses the "Train" button. This will add some slowness, but as we are preforming ML tasks which take a long time, it will probably get lost in the noise.

TODO: update the workQueue method to be a robust handler (reconnect if connection is lost). We can also change the connection paradigm to be asynchronus (haven't done this yet as I don't know how to integrate pika into the Dash IOLoop.)

TODO: Add json schema, so that we can test and garuntee that the commands being passed through the message queue are correct.
