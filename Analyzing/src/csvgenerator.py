import csv
import random
from datetime import datetime
import time
with open('health.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Date","BLANKET"])
    i = 0
    while i < 1000:
        writer.writerow([datetime.now().timestamp().__int__(),random.randint(0,60)])
        i = i + 1
        time.sleep(1)
