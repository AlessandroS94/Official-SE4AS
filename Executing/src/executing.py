import os
import threading
import time
from datetime import datetime
import pandas as pd
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

class Service(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.topicExecuting = "/channel/BLANKET-executing"
        self.client_id = f'python-mqtt-{8}'
        self.payload = []

    def connect_mqtt(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logging.info("Connected to MQTT Broker!")
            else:
                logging.info("Failed to connect, return code %d\n", rc)

        client = mqtt_client.Client(self.client_id)
        client.on_connect = on_connect
        client.connect(self.host, self.port)
        return client

    def subscribe(self, client: mqtt_client):

        def on_message(client, userdata, msg):
            print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
            logging.info(
                f"Received `{msg.payload.decode()}` from `{msg.topic}` topic -- {time.asctime(time.localtime(time.time()))}")
            try :
                if msg.topic == "/channel/BLANKET-executing":
                    with open("./executing.csv", 'a+') as f:
                        f.write("" + datetime.now().timestamp().__int__().__str__() + "," + msg.payload.decode() + "\n")
            except Exception as excM:
                logging.info(
                    f"Exception : {excM} -- {time.asctime(time.localtime(time.time()))}")
                pidP = os.getpid()
                os.kill(pidP, 2)

        client.subscribe(self.topicExecuting)
        client.on_message = on_message

    def run(self):
        client = self.connect_mqtt()
        self.subscribe(client)
        client.loop_forever()


class Executing(threading.Thread):

    def __init__(self, service):
        threading.Thread.__init__(self)
        self.service = service

    def connect_mqtt(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logging.info("Connected to MQTT Broker!")
            else:
                logging.info("Failed to connect, return code %d\n", rc)

        client = mqtt_client.Client(f'python-mqtt-{9}')

        client.on_connect = on_connect
        client.connect(self.service.host, self.service.port)
        return client

    def publish(self, client):
        while True:
            try:
                time.sleep(1)
                data = pd.read_csv("./executing.csv")
                data = pd.DataFrame(data, columns=['Date', 'BLANKET'])
                blanket = data['BLANKET'][(len(data)) - 1]
                result = client.publish("/channel/BLANKET-sensor", str(blanket))
                status = result[0]
                if status == 0:
                    print("Set blanket value:\n", blanket)
                    logging.info(f"Set blanket value: {blanket} -- {time.asctime(time.localtime(time.time()))}")
                else:
                    logging.info(
                        f"Failed to send message to topic /executing/BLANKET:  {blanket} -- {time.asctime(time.localtime(time.time()))}")
            except Exception as e:
                print('erorr' + e)
                logging.info(f"It has occurred this error:: {e}")
                pidP = os.getpid()
                os.kill(pidP, 2)

    def run(self):
        client = self.connect_mqtt()
        self.publish(client)


def main():
    with open("settings.yaml", 'r') as stream:
        try:
            settings = yaml.safe_load(stream)
            MOSQUITTODNS = settings['mosquittoDNS']
            MOSQUITTOPORT = settings['mosquittoPORT']
        except yaml.YAMLError as exc:
            print(exc)
            pidP = os.getpid()
            os.kill(pidP, 2)
    service = Service(MOSQUITTODNS, MOSQUITTOPORT)
    service.start()

    executing = Executing(service)
    executing.start()

    app.run(host="127.0.0.1", port="8081")


if __name__ == '__main__':
    main()
