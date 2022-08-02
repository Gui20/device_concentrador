from umqtt.robust import MQTTClient
from machine import UART
from time import sleep
import gc

gc.enable()
gc.collect()

WIFI_SSID = "Bruno"
WIFI_PW = "12345678"

CERT_FILE = "esp32-gui.cert.pem"
KEY_FILE = "esp32-gui.private.key"


MQTT_CLIENT_ID = "basicPubSub"
MQTT_HOST = "a189i0v27jb246-ats.iot.sa-east-1.amazonaws.com"
MQTT_PORT = 8883
MQTT_TOPIC = "sdk/test/Python"

def connect_wifi(ssid, pw):
    import network
    wlan = network.WLAN(network.STA_IF)
    
    if(wlan.isconnected()):
        wlan.disconnect()  
    nets = wlan.scan()
    
    if not wlan.isconnected():

        wlan.active(True)
        wlan.connect(WIFI_SSID, WIFI_PW)
        while not wlan.isconnected():
            pass
    print("connected at {}\n{}".format(ssid, wlan.ifconfig()))
    

mqtt_client = None

def pub_msg(msg):
    global mqtt_client
    try:    
        mqtt_client.publish(MQTT_TOPIC, msg)
        print("Sent: " + msg)
    except Exception as e:
        print("Exception publish: " + str(e))
        raise
    

def connect_mqtt():
    global mqtt_client

    with open("esp32-gui.cert.pem", "r") as f: 
        cert = f.read()
        print("Got Cert")
        
    with open("esp32-gui.private.key", "r") as f: 
        key = f.read()
        print("Got Key")
        

    mqtt_client = MQTTClient(client_id=MQTT_CLIENT_ID, server=MQTT_HOST, port=MQTT_PORT, keepalive=5000, ssl=True, ssl_params={"cert":cert, "key":key, "server_side":False})
    mqtt_client.connect()
    print('MQTT Connected')


def lendo_serial():
    serial = ''
    uart = UART(2, 9600)
    uart.init(9600, bits=8, parity=None, stop=1)
    uart.write(str.encode("HISTORY=1\r\n\n"))
    sleep(5)
    while True:
        aux = uart.read()
        aux = str(aux, 'utf-8')
        serial = serial + aux
        sleep(1)
        if uart.any() == 0:
            break
    return serial


#start execution
try:
    print("Connecting WIFI")
    connect_wifi(WIFI_SSID, WIFI_PW)
    print("Pegando os Dados")
    serial = lendo_serial()
    print("Connecting MQTT")
    connect_mqtt()
    print("Publishing")
    
    
    cont_anterior = 0
    cont_posterior = 400
    step = 400
    
    while True:
        pub_msg("{\"Concentrador\":" + serial[cont_anterior:cont_posterior] + "}")
        cont_anterior = cont_anterior + step
        cont_posterior = cont_posterior + step
        gc.collect()
        sleep(3)
        if cont_posterior >= len(serial):
            cont_posterior = len(serial)
            pub_msg("{\"Concentrador\":" + serial[cont_anterior:cont_posterior] + "}")
            gc.collect()
            break

    print("OK")
except Exception as e:
    print(str(e))
