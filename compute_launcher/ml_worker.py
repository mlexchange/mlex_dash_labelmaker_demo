import pika
import subprocess
import json
import os
import sys
import threading
from multiprocessing import Process
import functools
import logging

#LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName)'
#              '-35s %(lineno) -5d: %(message)s')
#LOGGER = logging.getLogger(__name__)
#logging = logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
logging.basicConfig()
LOGGER = logging.getLogger(__name__)
class dockerLaunch():
    """
    Object to handle launching docker instances
    """
    def __init__(self, launchSchema):
        pass


def launch_container(channel, delivery_tag, body):
    """
    Launch docker container using subprocess
    Args: 
        channel pika?: ml queue
        delivery_tag pika?: the unique id I think?
        body json?: docker command to run
    """
    fmt1 = 'Delivery tag: {} Message body: {}'
    LOGGER.info(fmt1.format(delivery_tag, body))

    # open file object for logging
    log_name = 'temp-{}.log'.format(delivery_tag)
    print("Recieved message: {}".format(body))
    payload = json.loads(body)
    with open(log_name, 'w') as fout:
        cmds = ''
        if payload['gpu'] == True:
            cmds = '--gpus all'
        try:
            print('starting command')
            cmd_run = ['docker', 'run', *cmds.split(), '--rm', '-v', '{}:/data'.format(DATA_DIR), payload['docker_uri'], *payload['docker_cmd'].split(), *payload['kw_args'].split()]
            print('running command: {}'.format(cmd_run))
            logs = subprocess.run(cmd_run, text=True, check=True, stdout=fout)
        except Exception as e:
            print('process failed {}'.format(e))
    # read logs and print them to see what happened
    with open(log_name, 'r') as fin:
        print(logs)
        print(fin.read())

    channel.basic_ack(delivery_tag=delivery_tag)
    return logs

if __name__ == '__main__':
    AMQP_URL = os.environ['AMQP_URL']
    DATA_DIR = os.environ['DATA_DIR']
    params = pika.URLParameters(AMQP_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    result = channel.queue_declare(queue='ml_tasks', durable=True)

    def on_message(channel, method_frame, header_frame, body, args):
        (connection, threads) = args
        delivery_tag = method_frame.delivery_tag


    def callback(ch, method, properties, body):
        """pika callback function-- run when message is recieved
        """
        print("Recieved message: {}".format(body))
        payload = json.loads(body)
        #logs = subprocess.run(sub_commands, text=True, check=True)
        #logs = subprocess.run(['docker', 'run','-v', '{}:/data'.format(DATA_DIR), payload['docker_uri'], payload['docker_cmd'], *payload['kw_args'].split() ], text=True, check=True, stdout=subprocess.PIPE)
        cmds = ''
        if payload['gpu'] == True:
            cmds = '--gpus all'
        else:
            cmds = ''
        try:
            logging.info('launching container')
          #  logs = subprocess.run(['docker', 'run', *cmds.split(), '--rm', '-v', '{}:/data'.format(DATA_DIR), payload['docker_uri'], *payload['docker_cmd'].split(), *payload['kw_args'].split() ], text=True, check=True, stdout=subprocess.PIPE)
            #logs = launch_container(ch, method.delivery_tag, body)
            p = Process(launch_container,ch, method.delivery_tag, body)
            p.start()
            logging.info('container_launched')

#            print(logs)
            ch.basic_ack(delivery_tag = method.delivery_tag)

        #now send message back
            payload_back = {
                    'job_type': payload['job_type'],
                    'job_status':'complete', 
                    'logs':'done'} #str(logs.stdout)}
            payload_back = json.dumps(payload)
            ch.basic_publish(exchange='',
                    routing_key = properties.reply_to,
                    properties = pika.BasicProperties(correlation_id = properties.correlation_id),
                    body=payload_back,
                    )
            print('send logs back')
        except Exception as e:
            print('task failed, check logs')
            print(e)
            #print(str(e.stdout))
            payload = {'error':str(e),
                    'log':str(e)
                    }
            ch.basic_ack(delivery_tag = method.delivery_tag)
            ch.basic_publish(exchange='',
                    routing_key = properties.reply_to,
                    properties = pika.BasicProperties(correlation_id = properties.correlation_id),
                    body=json.dumps(payload),
                    ) #need to return something, or the dash app will hang and throw an error when the callback doesn't finish
    channel.basic_consume(queue="ml_tasks", on_message_callback=callback)
    print("Worker up. Waiting for tasks...")
    try:
        channel.start_consuming()


    except KeyboardInterrupt:
        print("Interrupt!")
        channel.stop_consuming()
        connection.close()

        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)


    

