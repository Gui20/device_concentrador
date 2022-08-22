"""
Firmware: 7050000003
Data: 15/08/2022
Author: Guilherme Cardoso Coelho
email:gcoelho@ioutility.com.br / coelho.gui19@gmail.com

"""

import gc
import network
import os
from machine import Pin, SPI, UART 
from sdcard import SDCard
from umqtt.robust import MQTTClient
from time import sleep
import json

class Executa():
    
    WIFI_SSID = "Gui-Ioutility-wifi"
    WIFI_PW = "12345678"
    
    
    CERT_FILE = "180c0b2382822429f1f8fe4344c2f5b1d722b9c3098c481749ea824fb477f813-certificate.pem"
    KEY_FILE = "180c0b2382822429f1f8fe4344c2f5b1d722b9c3098c481749ea824fb477f813-private.pem.key"
    

    MQTT_CLIENT_ID = "concentrador-1"
    MQTT_HOST = "a189i0v27jb246-ats.iot.sa-east-1.amazonaws.com"
    MQTT_PORT = 8883
    MQTT_TOPIC = "esp32/concentrador-1"


    def __init__(self, WIFI_SSID, WIFI_PW, CERT_FILE, KEY_FILE, MQTT_CLIENT_ID, MQTT_HOST, MQTT_PORT, MQTT_TOPIC):
        self.WIFI_SSID = WIFI_SSID
        self.WIFI_PW = WIFI_PW
        
        self.CERT_FILE = CERT_FILE
        self.KEY_FILE = KEY_FILE
        
        self.MQTT_CLIENT_ID = MQTT_CLIENT_ID
        self.MQTT_HOST = MQTT_HOST
        self.MQTT_PORT = MQTT_PORT
        self.MQTT_TOPIC = MQTT_TOPIC
        
    def conecta_wifi(self):
        wlan = network.WLAN(network.STA_IF)
        
        if wlan.isconnected():
            wlan.disconnect()
        if not wlan.isconnected():
            wlan.active(True)

            wlan.connect(self.WIFI_SSID, self.WIFI_PW)
            while not wlan.isconnected():
                pass

        print("connected at {}".format(self.WIFI_SSID))
        gc.collect()
        
    def sd_setup(self):
        spisd = SPI(-1, miso=Pin(13), mosi=Pin(12), sck=Pin(14))
        sd = SDCard(spisd, Pin(27))
        
        vfs = os.VfsFat(sd)
        os.mount(vfs, '/sd')
        os.chdir('/sd')
    def conecta_mqtt(self):
        
        global mqtt_client
        gc.enable()
        gc.collect()
        os.chdir('/')
        with open("180c0b2382822429f1f8fe4344c2f5b1d722b9c3098c481749ea824fb477f813-certificate.pem", "r") as f:
            cert = f.read()
            print("Got Cert")
            
        with open("180c0b2382822429f1f8fe4344c2f5b1d722b9c3098c481749ea824fb477f813-private.pem.key", "r") as f: 
            key = f.read()
            print("Got Key")
            
        mqtt_client = MQTTClient(client_id=self.MQTT_CLIENT_ID, server=self.MQTT_HOST, port=self.MQTT_PORT, keepalive=5000, ssl=True, ssl_params={"cert":cert, "key":key, "server_side":False})
        # IndexError: list index out of range -> Talvez seja internet.
        try:
            mqtt_client.connect()
        except IndexError as e:
            sleep(5)
            print("Reconectando...")
            self.conecta_wifi()
            print("Conectando MQTT novamente...")
            self.conecta_mqtt()
            
        gc.enable()
        gc.collect()
        print('MQTT Connected')
        
    # Variável que se tornará global

    mqtt_client = None

    # Função de publicação de mensagem via MQTT

    def pub_msg(self, msg):
        
        global mqtt_client
        gc.enable()
        gc.collect()
        
        try:    
            mqtt_client.publish(self.MQTT_TOPIC, msg)
        except Exception as e:
            print("Exception publish: " + str(e))
            raise
    def lendo_serial(self):
        
        os.chdir('/sd')
        f = open('data.txt', 'w')
        f.write('')
        f.close()
        
        gc.enable()
        gc.collect()
        serial = ''
        uart = UART(2, 9600)
        uart.init(9600, bits=8, parity=None, stop=1, rxbuf=3020)
        # Lê buffer antes de começar a leitura de fato
        while True:
            z = uart.read()
            print(z)
            sleep(3)
            if uart.any() == 0:
                break
            sleep(1)
            
        uart.write(b"HISTORY=1\r\n\n")
        
        sleep(2)
        while True:
            gc.collect()        
            aux = uart.read()
            # print(aux)
            try:           
                aux = str(aux, 'utf-8')
                gc.collect()           
            except TypeError as e:
                # Esse erro se dá pq as vezes aux é igual a None e na hora de converter ele não converte e da erro.
                print("Corrigindo-> Type Error: {} ...".format(e))
                sleep(15)
                uart.deinit()
                gc.enable()
                gc.collect()
                return self.lendo_serial()     
            except UnicodeError as f:
                # Este erro acontece pq as vezes ele lê da uart alguns dados hex + bytes e não consegue converter
                print("Corrigindo -> UnicodeError: ... ")
                sleep(15)
                uart.deinit()
                gc.enable()
                gc.collect()
                return self.lendo_serial() 
            try:
                os.chdir('/sd')
                f = open('data.txt', 'a')
                print(aux)
                f.write(aux)
                f.close()
                print(aux)
                aux = gc.collect()
                gc.collect()           
            except TypeError as e:
                print(e)
            sleep(3)
            gc.enable()
            gc.collect()
            if uart.any() == 0:           
                uart.deinit()
                gc.enable()
                gc.collect()
                break
        os.chdir('/sd')
        f = open('data.txt', 'r')
        s = f.read(33)
        if s[11:33] == "Start of log transfer;":
            gc.collect()
            f.close()
            return True
        else:
            # Se retornar falso é pq passou pelos erros e não começou com a string correta, de um sleep de um tempo bom e tente dnv
            return False
    def main(self):
        # Início da Execução
        try:
            gc.enable()
            gc.collect()
        
            # self.sd_setup()
            print("Pegando os Dados...")
            
            while True:
                gc.collect()

                try:
                    serial = self.lendo_serial()
                    gc.collect()
                    if not serial:
                        print("Corrigindo erro de quebra de dados...")
                        sleep(20)
                        serial = self.lendo_serial()
                    else:
                        break
                except MemoryError as e:
                    import machine
                    print("Memory Error: {}".format(e))
                    machine.reset()
            print("Conectando WIFI...")
            self.conecta_wifi()
            print("Conectando MQTT...")
            self.conecta_mqtt()
            print("Publicando na AWS IoT...")
            
            os.chdir('/sd')
            f = open('data.txt', 'r')
            gc.enable()
            gc.collect()
            while True:
                gc.enable()
                gc.collect()
                s = f.read(400)
                s = s + f.read(400)
                data = json.dumps({"Concentrador": s})
                # print(data)
                self.pub_msg(data)
                sleep(3)
                if 'End of log transfer;' in s:
                    gc.enable()
                    gc.collect()
                    f.close()
                    break
                s = ''
            print("OK")
        except Exception as e:
            print(str(e))
