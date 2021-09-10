import threading
import pandas as pd
import numpy as np
import time
from datetime import datetime
import os
import yaml
from sklearn.linear_model import LinearRegression
import logging
from paho.mqtt import client as mqtt_client
from flask import Flask

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
        self.topicHR = "/channel/HR-sensor"
        self.topicTEMP = "/channel/TEMP-sensor"
        self.topicBLANKET = "/channel/BLANKET-sensor"
        self.topicPrevisioning = "/channel/BLANKET-prediction"
        self.dataset = './health.csv'
        self.client_id = f'python-mqtt-{3}'
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
            print(
                f"Received `{msg.payload.decode()}` from `{msg.topic}` topic -- {time.asctime(time.localtime(time.time()))}")
            logging.info(
                f"Received `{msg.payload.decode()}` from `{msg.topic}` topic -- {time.asctime(time.localtime(time.time()))}")
            try:
                if msg.topic == "/channel/BLANKET-sensor":
                    with open(self.dataset, 'a+') as f:
                        f.write("" + datetime.now().timestamp().__int__().__str__())
                    with open('./health.csv', 'a+') as f:
                        f.write("," + msg.payload.decode())
                    with open(self.dataset, 'a+') as f:
                        f.write("\n")
            except Exception as excM:
                logging.info(
                    f"Exeption: {excM} -- {time.asctime(time.localtime(time.time()))}")
                pidP = os.getpid()
                os.kill(pidP, 2)

        client.subscribe(self.topicBLANKET)
        client.on_message = on_message

    def run(self):
        client = self.connect_mqtt()
        self.subscribe(client)
        client.loop_forever()


class ML(threading.Thread):

    def __init__(self,service):
        threading.Thread.__init__(self)
        self.service = service

    def connect_mqtt(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logging.info("Connected to MQTT Broker!")
            else:
                logging.info("Failed to connect, return code %d\n", rc)

        try:
            client = mqtt_client.Client(f'python-mqtt-{4}')
            client.on_connect = on_connect
            client.connect(self.service.host, self.service.port)
            return client
        except Exception as excM:
            logging.info(f"Execption: {excM} -- {time.asctime(time.localtime(time.time()))}")
            pidP = os.getpid()
            os.kill(pidP, 2)

    def publish(self, client):
        while True:
            try:
                time.sleep(10)
                data = pd.read_csv(self.service.dataset)
                data = pd.DataFrame(data, columns=['Date', 'BLANKET'])
                X = np.array(data)[:, 0].reshape(-1, 1)
                y = np.array(data)[:, 1].reshape(-1, 1)
                to_predict_x = [data['Date'][len(data['Date']) - 1] + 1]
                to_predict_x = np.array(to_predict_x).reshape(-1, 1)
                regsr = LinearRegression()
                regsr.fit(X, y)
                predicted_y = regsr.predict(to_predict_x)
                result = client.publish("/channel/BLANKET-prediction", str(predicted_y.__int__()))
                status = result[0]
                if status == 0:
                    print("Predicted blanket value:\n", predicted_y.__int__())
                    logging.info(
                        f"Predicted blanket value: {predicted_y.__int__()} -- {time.asctime(time.localtime(time.time()))}")
                else:
                    logging.info(
                        f"Failed to send message to topic {predicted_y.__int__()} -- {time.asctime(time.localtime(time.time()))}")
                    logging.info(result)
            except Exception as exceptionM:
                logging.info(
                    f"Exeptionc {exceptionM} -- {time.asctime(time.localtime(time.time()))}")
                pidP = os.getpid()
                os.kill(pidP, 2)


    def run(self):
        client = self.connect_mqtt()
        self.publish(client)


def main():
    with open("./settings.yaml", 'r') as stream:
        try:
            settings = yaml.safe_load(stream)
            MOSQUITTODNS = settings['mosquittoDNS']
            MOSQUITTOPORT = settings['mosquittoPORT']
        except yaml.YAMLError as exc:
            logging.info(f"Failed to reading settings-- {time.asctime(time.localtime(time.time()))}")
            pidP = os.getpid()
            os.kill(pidP, 2)
    service = Service(MOSQUITTODNS, MOSQUITTOPORT)
    service.start()
    ml = ML(service)
    ml.start()

    # Container
    app.run(host="127.0.0.1", port="8080")
    service.join()
    ml.join()

if __name__ == '__main__':
    main()
