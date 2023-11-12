#!/usr/bin/python3

import asyncio
import sys

from bleak import BleakClient, BleakScanner
import logging
import codecs
import requests
import aiohttp
import threading

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

ADDRESS = "A0:B7:65:DD:82:7E"

TEMPERATURE_UUID = "1c95d5e3-d8f7-413a-bf3d-7a2e5d7be87e"
HUMIDITY_UUID = "f639b61e-f796-11ed-b67e-0242ac120002"
LIGHT_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

BASE_URL = "https://smathome.asia/api/"

logger = logging.getLogger(__name__)

async def main(address, token, db):
    header = {'Authorization' : 'Bearer ' + token}
    url = BASE_URL + "device-monitor"
    
    while True:
        logger.debug("scanning for device")
        device = await BleakScanner.find_device_by_address(address)
        
        if device is None:
            logger.debug("no device found, wait then scan again")
            await asyncio.sleep(30)
            continue
        
        disconnect_event = asyncio.Event()
        
        try:
            async with BleakClient(address, winrt=dict(use_cached_services=True)) as client:
                logger.debug("connecting to device")
                    
                while True:
                    light_doc = db.get()
                    action = light_doc.get('action')
                    print(light_doc.get('action'))
                    await client.write_gatt_char(LIGHT_UUID, bytearray(action.encode('utf-8')), response=False)
                    
                    temperature = await client.read_gatt_char(TEMPERATURE_UUID)
                    print("Temperature: {0}".format(codecs.decode(temperature, 'utf-8')))
            
                    humidity = await client.read_gatt_char(HUMIDITY_UUID)
                    print("Humidity: {0}".format(codecs.decode(humidity, 'utf-8')))
                    
                    dataTemperature = {'value' : str(codecs.decode(temperature, 'utf-8')), 'unitMeasure' : 'C', 'deviceDTO': {'id' : '654b8ec3137e6c2f34d96add'}}
                    postData(dataTemperature, header, url)
                    
                    dataHumidity = {'value' : str(codecs.decode(humidity, 'utf-8')), 'unitMeasure' : '%', 'deviceDTO': {'id' : '654f92f66ea8397e0c693e0a'}}
                    postData(dataHumidity, header, url)
                    await asyncio.sleep(60)
            
        except Exception:
            logger.exception("exception while connecting/connected")
    
async def authentication():
    url = BASE_URL + "authenticate"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json = {'username':'user','password':'user','rememberMe':True}) as resp:
           response = await resp.json()
           return response['id_token']

        
def postData(data, header, url):
    requests.post(url, headers=header, json=data)
       
if __name__ == "__main__":
    cred = credentials.Certificate('/home/pi/ble/smarthome-3db14-firebase-adminsdk-gz6fg-d587bc5a17.json')
    app = firebase_admin.initialize_app(cred)

    db = firestore.client()
    
    light = db.collection("develop").document("device_action").collection("user").document("654f92eb6ea8397e0c693e09")
    
    token = asyncio.run(authentication())
    
    if(token is not None):
        asyncio.run(main(ADDRESS, token, light))

