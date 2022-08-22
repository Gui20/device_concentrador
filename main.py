from executa import Executa
from time import sleep
import os
import gc
import json
from umqtt.robust import MQTTClient

# Executa(SSID, PSW, Certificado AWS IoT, Chave AWS IoT, "basicPubSub", "a189i0v27jb246-ats.iot.sa-east-1.amazonaws.com", 8883, Tópico Device Shadow)
x = Executa("Gui-Ioutility-wifi", "12345678", "180c0b2382822429f1f8fe4344c2f5b1d722b9c3098c481749ea824fb477f813-certificate.pem", "180c0b2382822429f1f8fe4344c2f5b1d722b9c3098c481749ea824fb477f813-private.pem.key", "concentrador-1", "a189i0v27jb246-ats.iot.sa-east-1.amazonaws.com", 8883, "esp32/concentrador-1")

os.chdir('/')
sleep(2)
x.sd_setup()

while True:
    gc.collect()
    print('Utilização de Memória: {} '.format(gc.mem_free()))
    try:
        x.main()
    except:
        import machine
        machine.reset()
          
    # A cada 5 min
    sleep(300)


