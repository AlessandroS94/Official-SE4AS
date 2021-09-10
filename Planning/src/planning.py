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
        self.client_id = f'python-mqtt-{5}'
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
        # get all info
        def on_message(client, userdata, msg):
            print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
            logging.info(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
            try:
                if msg.topic == '/channel/TEMPERATURE-max-limit':
                    with open("CONTROL-MAX-temperature.csv", 'a+') as f:
                        f.write("" + datetime.now().timestamp().__int__().__str__() + "," + msg.payload.decode() + "\n")
                if msg.topic == '/channel/TEMPERATURE-min-limit':
                    with open("CONTROL-MIN-temperature.csv", 'a+') as f:
                        f.write("" + datetime.now().timestamp().__int__().__str__() + "," + msg.payload.decode() + "\n")
                if msg.topic == '/channel/TEMP-sensor':
                    with open("./TEMP-sensor.csv", 'a+') as f:
                        f.write("" + datetime.now().timestamp().__int__().__str__() + "," + msg.payload.decode() + "\n")
                if msg.topic == '/channel/BLANKET-prediction':
                    with open("./BLANKET-prediction.csv", 'a+') as f:
                        f.write("" + datetime.now().timestamp().__int__().__str__() + "," + msg.payload.decode() + "\n")
                if msg.topic == '/channel/BLANKET-sensor':
                    with open("./BLANKET-sensor.csv", 'a+') as f:
                        f.write("" + datetime.now().timestamp().__int__().__str__() + "," + msg.payload.decode() + "\n")
                if msg.topic == '/channel/HR-sensor':
                    with open("./HR-sensor.csv", 'a+') as f:
                        f.write("" + datetime.now().timestamp().__int__().__str__() + "," + msg.payload.decode() + "\n")
            except Exception as excM:
                logging.info(
                    f"Exeption: {excM} -- {time.asctime(time.localtime(time.time()))}")
                pidP = os.getpid()
                os.kill(pidP, 2)

        client.subscribe('/channel/TEMPERATURE-max-limit')
        client.on_message = on_message

        client.subscribe('/channel/TEMPERATURE-min-limit')
        client.on_message = on_message

        client.subscribe('/channel/TEMP-sensor')
        client.on_message = on_message

        client.subscribe('/channel/BLANKET-prediction')
        client.on_message = on_message

        client.subscribe('/channel/BLANKET-sensor')
        client.on_message = on_message

        client.subscribe('/channel/HR-sensor')
        client.on_message = on_message

    def run(self):
        client = self.connect_mqtt()
        self.subscribe(client)
        client.loop_forever()


class Planning(threading.Thread):

    def __init__(self, service, MINTEMPERATUREBLANKET, MAXTEMPERATUREBLANKET,INTERVALLEVEL1,INTERVALLEVEL2, HRMIN, HRMAX):
        threading.Thread.__init__(self)
        self.service = service
        self.MINTEMPERATUREBLANKET = MINTEMPERATUREBLANKET
        self.MAXTEMPERATUREBLANKET = MAXTEMPERATUREBLANKET
        self.HRMIN = HRMIN
        self.HRMAX = HRMAX
        self.INTERVALLEVEL1 = INTERVALLEVEL1
        self.INTERVALLEVEL2 = INTERVALLEVEL2
    def connect_mqtt(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logging.info("Connected to MQTT Broker!")
            else:
                logging.info("Failed to connect, return code %d\n", rc)

        try:
            client = mqtt_client.Client(f'python-mqtt-{6}')
            client.on_connect = on_connect
            client.connect(self.service.host, self.service.port)
            return client
        except Exception as excM:
            logging.info(f"Execption: {excM} -- {time.asctime(time.localtime(time.time()))}")
            pidP = os.getpid()
            os.kill(pidP, 2)

    # convert to integer and check temperature
    def checkRange(self, blanket, actual, minimum, maximum, hr, prevision):
        actual = int(actual)
        minimum = int(minimum)
        maximum = int(maximum)
        hr = int(hr)
        blanket = int(blanket)
        prevision = int(prevision)
        # normale
        if minimum < actual < maximum:
            return prevision
        # battiti + hr bassi
        elif actual <= minimum:
            if prevision > (blanket + self.INTERVALLEVEL1):
                return prevision
            if hr < self.HRMIN:
                return blanket+self.INTERVALLEVEL1
            else:
                return blanket + self.INTERVALLEVEL1

        elif actual >= maximum:
            if prevision < (blanket - self.INTERVALLEVEL2):
                return prevision
            if hr > self.HRMIN:
                return blanket-self.INTERVALLEVEL2
            else:
                return blanket - self.INTERVALLEVEL1

        elif actual < maximum and hr > self.HRMAX:
            return blanket

        return prevision


    def respectBlanketSettings(self,blanket):
        if blanket < self.MINTEMPERATUREBLANKET:
            return self.MINTEMPERATUREBLANKET
        if blanket >self.MAXTEMPERATUREBLANKET:
            return self.MAXTEMPERATUREBLANKET
        else:
            return blanket


    def publish(self, client):
        while True:
            try:
                time.sleep(1)
                dataPREVISIONING = pd.read_csv("./BLANKET-prediction.csv")
                dataPREVISIONING = pd.DataFrame(dataPREVISIONING, columns=['Date', 'PREDICT'])
                dataBLANKETSENSOR = pd.read_csv("./BLANKET-sensor.csv")
                dataBLANKETSENSOR = pd.DataFrame(dataBLANKETSENSOR, columns=['Date', 'TEMP'])
                dataCONTROLMAX = pd.read_csv("CONTROL-MAX-temperature.csv")
                dataCONTROLMAX = pd.DataFrame(dataCONTROLMAX, columns=['Date', 'TEMP'])
                dataCONTROLMIN = pd.read_csv("CONTROL-MIN-temperature.csv")
                dataCONTROLMIN = pd.DataFrame(dataCONTROLMIN, columns=['Date', 'TEMP'])
                dataHRSENSOR = pd.read_csv("./HR-sensor.csv")
                dataHRSENSOR = pd.DataFrame(dataHRSENSOR, columns=['Date', 'HR'])
                dataTEMPSENSOR = pd.read_csv("./TEMP-sensor.csv")
                dataTEMPSENSOR = pd.DataFrame(dataTEMPSENSOR, columns=['Date', 'TEMP'])

                blanket = self.checkRange(dataBLANKETSENSOR['TEMP'][(len(dataBLANKETSENSOR)) - 1],
                                             dataTEMPSENSOR['TEMP'][(len(dataTEMPSENSOR)) - 1],
                                             dataCONTROLMIN['TEMP'][(len(dataCONTROLMIN)) - 1],
                                             dataCONTROLMAX['TEMP'][(len(dataCONTROLMAX)) - 1],
                                             dataHRSENSOR['HR'][(len(dataHRSENSOR)) - 1],
                                             dataPREVISIONING['PREDICT'][(len(dataPREVISIONING)) - 1])
                print(dataBLANKETSENSOR['TEMP'][(len(dataBLANKETSENSOR)) - 1],
                                             dataTEMPSENSOR['TEMP'][(len(dataTEMPSENSOR)) - 1],
                                             dataCONTROLMIN['TEMP'][(len(dataCONTROLMIN)) - 1],
                                             dataCONTROLMAX['TEMP'][(len(dataCONTROLMAX)) - 1],
                                             dataHRSENSOR['HR'][(len(dataHRSENSOR)) - 1],
                                             dataPREVISIONING['PREDICT'][(len(dataPREVISIONING)) - 1])
                blanket = self.respectBlanketSettings(blanket)
                result = client.publish("/channel/BLANKET-executing", str(blanket))
                status = result[0]

                if status == 0:
                    print("Set blanket value:\n", blanket)
                    logging.info(f"Set blanket value: {blanket} -- {time.asctime(time.localtime(time.time()))}")
                else:
                    logging.info(
                        f"Failed to send message to topic /executing/BLANKET:  {blanket} -- {time.asctime(time.localtime(time.time()))}")
            except Exception as exceptionM:
                logging.info(
                    f"Exeptionc {exceptionM} -- {time.asctime(time.localtime(time.time()))}")
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
            MINTEMPERATUREBLANKET = settings['MINTEMPERATUREBLANKET']
            MAXTEMPERATUREBLANKET = settings['MAXTEMPERATUREBLANKET']
            HRMIN = settings['HRMIN']
            HRMAX = settings['HRMAX']
            INTERVALLEVEL1 = settings['INTERVALLEVEL1']
            INTERVALLEVEL2 = settings['INTERVALLEVEL2']

        except yaml.YAMLError as exc:
            logging.info(f"Failed to reading settings-- {time.asctime(time.localtime(time.time()))}")
            pidP = os.getpid()
            os.kill(pidP, 2)
    service = Service(MOSQUITTODNS, MOSQUITTOPORT)
    service.start()
    time.sleep(4)
    plan = Planning(service, MINTEMPERATUREBLANKET, MAXTEMPERATUREBLANKET,INTERVALLEVEL1,INTERVALLEVEL2, HRMIN, HRMAX)
    plan.start()
    # Local Run
    #app.run(host="127.0.0.1", port="8082")


if __name__ == '__main__':
    main()
