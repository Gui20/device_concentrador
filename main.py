from umqtt.robust import MQTTClient
from machine import UART
from time import sleep
import gc
import json
import network


# Habilita alocação de memória

gc.enable()
gc.collect()

# Credenciais de conexão Wifi

WIFI_SSID = "Bruno"
WIFI_PW = "12345678"

# Certificado e Chave para autenticação SSL da AWS IoT

CERT_FILE = "esp32-gui.cert.pem"
KEY_FILE = "esp32-gui.private.key"

# Credenciais para conexão MQTT na AWS IoT

MQTT_CLIENT_ID = "basicPubSub"
MQTT_HOST = "a189i0v27jb246-ats.iot.sa-east-1.amazonaws.com"
MQTT_PORT = 8883
MQTT_TOPIC = "sdk/test/Python"


# Função conecta wifi

def conecta_wifi(ssid, pw):
    wlan = network.WLAN(network.STA_IF)
    
    if wlan.isconnected():
        wlan.disconnect()
    else:
        wlan.active(True)
        wlan.connect(WIFI_SSID, WIFI_PW)
        while not wlan.isconnected():
            pass
    print("connected at {}".format(ssid))
    

def lendo_serial():
    
    gc.enable()
    gc.collect()
    serial = ''
    uart = UART(2, 9600)
    uart.init(9600, bits=8, parity=None, stop=1, rxbuf=3020)
    # As vezes da esse erro: object with buffer protocol required - precisa tratar
    uart.write(str.encode("HISTORY=1\r\n\n"))
    sleep(4)
    while True:
        aux = uart.read()
        aux = str(aux, 'utf-8')
        serial = serial + aux
        sleep(1)
        gc.enable()
        gc.collect()
        if uart.any() == 0:
            uart.deinit()
            gc.enable()
            gc.collect()
            break
    return serial


# Variável que se tornará global

mqtt_client = None


# Função que conecta via MQTT da Amazon

def conecta_mqtt():
    global mqtt_client
    gc.enable()
    gc.collect()
    with open("esp32-gui.cert.pem", "r") as f: 
        cert = f.read()
        print("Got Cert")
        
    with open("esp32-gui.private.key", "r") as f: 
        key = f.read()
        print("Got Key")
    # As vezes da o seguinte erro: list index out of range - precisa tratar
    
    mqtt_client = MQTTClient(client_id=MQTT_CLIENT_ID, server=MQTT_HOST, port=MQTT_PORT, keepalive=5000, ssl=True, ssl_params={"cert":cert, "key":key, "server_side":False})
    mqtt_client.connect()

    gc.enable()
    gc.collect()
    print('MQTT Connected')


# Função de publicação de mensagem via MQTT

def pub_msg(msg):
    global mqtt_client
    gc.enable()
    gc.collect()
    
    try:    
        mqtt_client.publish(MQTT_TOPIC, msg)
    except Exception as e:
        print("Exception publish: " + str(e))
        raise


# Início da Execução

try:
    gc.enable()
    gc.collect()
    print("Conectando WIFI...")
    conecta_wifi(WIFI_SSID, WIFI_PW)
    print("Pegando os Dados...")
    serial = lendo_serial()
    print("Conectando MQTT")
    conecta_mqtt()
    print("Publicando na AWS IoT...")
    
    
    cont_anterior = 0
    cont_posterior = 400
    step = 400
    gc.enable()
    gc.collect()
    while True:
        gc.enable()
        gc.collect()
        data = json.dumps({"Concentrador": serial[cont_anterior:cont_posterior]})
        pub_msg(data)
        
        
        cont_anterior = cont_anterior + step
        cont_posterior = cont_posterior + step
        gc.enable()
        gc.collect()
        sleep(3)
        if cont_posterior >= len(serial):
            cont_posterior = len(serial)
            data = json.dumps({"Concentrador": serial[cont_anterior:cont_posterior]})
            pub_msg(data)
            # pub_msg("{\"Concentrador\":" + serial[cont_anterior:cont_posterior] + "}")
            gc.enable()
            gc.collect()
            break
    mqtt_client.disconnect()
    print("OK")
except Exception as e:
    print(str(e))
    import machine
    machine.reset()
