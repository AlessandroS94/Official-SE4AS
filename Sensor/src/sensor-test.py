import os
import random
import time
import logging
import yaml
from flask import Flask
from paho.mqtt import client as mqtt_client

logging.basicConfig(level=logging.DEBUG, filename="logfile", filemode="a+",
                    format="%(asctime)-15s %(levelname)-8s %(message)s")

app = Flask(__name__)


@app.route('/isAlive')
def index():
    return "true"


with open("settings.yaml", 'r') as stream:
    try:
        settings = yaml.safe_load(stream)
        MOSQUITTODNS = settings['mosquittoDNS']
        MOSQUITTOPORT = settings['mosquittoPORT']
    except yaml.YAMLError as exc:
        print(exc)
        pidP = os.getpid()
        os.kill(pidP, 9)

broker = MOSQUITTODNS
port = MOSQUITTOPORT

# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{1}'
topicHR = "/channel/HR-sensor"
topicTEMP = "/channel/TEMP-sensor"


# topicBLANKET = "/channel/BLANKET-sensor"

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to MQTT Broker!")
        else:
            logging.info("Failed to connect, return code %d\n", rc)

    try:
        client = mqtt_client.Client(f'python-mqtt-{2}')
        client.on_connect = on_connect
        client.connect(broker, port)
        return client

    except Exception as excM:
        logging.info(f"Execption: {excM} -- {time.asctime(time.localtime(time.time()))}")
        pidP = os.getpid()
        os.kill(pidP, 9)


def publish(client):
    client.publish("/channel/BLANKET-sensor", 30)
    while True:
        time.sleep(3)
        msgHR = random.randint(30, 180)
        result = client.publish(topicHR, msgHR)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            logging.info(f"Send `{msgHR}` to topic `{topicHR}` -- {time.asctime(time.localtime(time.time()))}")
        else:
            logging.info(f"Failed to send message to topic {topicHR} -- {time.asctime(time.localtime(time.time()))}")
        msgTEMP = random.randint(30, 43)
        result = client.publish(topicTEMP, msgTEMP)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            logging.info(f"Send `{msgTEMP}` to topic `{topicTEMP}` -- {time.asctime(time.localtime(time.time()))}")
        else:
            logging.info(f"Failed to send message to topic {topicTEMP} -- {time.asctime(time.localtime(time.time()))}")


def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)
    # Local Run
    app.run(host="127.0.0.1", port="8083")


if __name__ == '__main__':
    run()

