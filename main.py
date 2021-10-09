#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import random
import asyncio
import yaml
import logging.config

import src.telldus as telldus
import tellcore.telldus as td
import tellcore.constants as const

from paho.mqtt import client as mqtt_client


TYPES = {const.TELLSTICK_TEMPERATURE: 'temperature',
         const.TELLSTICK_HUMIDITY: 'humidity',
         const.TELLSTICK_RAINRATE: 'rainrate',
         const.TELLSTICK_RAINTOTAL: 'raintotal',
         const.TELLSTICK_WINDDIRECTION: 'winddirection',
         const.TELLSTICK_WINDAVERAGE: 'windaverage',
         const.TELLSTICK_WINDGUST: 'windgust'}

METHODS = {const.TELLSTICK_TURNON: 'turn on',
           const.TELLSTICK_TURNOFF: 'turn off',
           const.TELLSTICK_BELL: 'bell',
           const.TELLSTICK_TOGGLE: 'toggle',
           const.TELLSTICK_DIM: 'dim',
           const.TELLSTICK_LEARN: 'learn',
           const.TELLSTICK_EXECUTE: 'execute',
           const.TELLSTICK_UP: 'up',
           const.TELLSTICK_DOWN: 'down',
           const.TELLSTICK_STOP: 'stop'}


def connect_mqtt(config, client_id) -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to MQTT Broker!")
        else:
            logging.critical("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(config['mqtt']['user'], config['mqtt']['pass'])
    client.on_connect = on_connect
    client.connect(config['mqtt']['broker'], int(config['mqtt']['port']))

    return client


def publish_mqtt(client, topic, msg):
    time.sleep(1)

    result = client.publish(topic, msg, retain=True)

    if result[0] == 0:
        logging.info(f"Send `{msg}` to topic `{topic}`")
    else:
        logging.error(f"Failed to send message to topic {topic}")


def subscribe_device(client: mqtt_client):
    def on_message(client, userdata, msg):
        logging.info(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        id = msg.topic.split('/')[1]
        cmd_status = False

        if int(msg.payload.decode()) == int(const.TELLSTICK_TURNON):
            logging.debug('[DEVICE] Sending command ON to device id {}'.format(id))
            cmd_status = d.turn_on(id)

        if int(msg.payload.decode()) == int(const.TELLSTICK_TURNOFF):
            logging.debug('[DEVICE] Sending command OFF to device id {}'.format(id))
            cmd_status = d.turn_off(id)

        # TODO: Need to find out what Home Assistant sends to dim...
        # https://www.home-assistant.io/integrations/light.mqtt/
        value = int(0)
        if int(msg.payload.decode()) == int(const.TELLSTICK_DIM):
            logging.debug('[DEVICE] Sending command DIM "{}" to device id {}'.format(id, value))
            logging.info('[DEVICE] MSG = {}'.format(msg))
            cmd_status = d.dim(id, value)

        if int(msg.payload.decode()) == int(const.TELLSTICK_BELL):
            logging.debug('[DEVICE] Sending command BELL to device id {}'.format(id))
            cmd_status = d.bell(id)

        if int(msg.payload.decode()) == int(const.TELLSTICK_EXECUTE):
            logging.debug('[DEVICE] Sending command EXECUTE to device id {}'.format(id))
            cmd_status = d.execute(id)

        if int(msg.payload.decode()) == int(const.TELLSTICK_UP):
            logging.debug('[DEVICE] Sending command UP to device id {}'.format(id))
            cmd_status = d.up(id)

        if int(msg.payload.decode()) == int(const.TELLSTICK_DOWN):
            logging.debug('[DEVICE] Sending command DOWN to device id {}'.format(id))
            cmd_status = d.down(id)

        if int(msg.payload.decode()) == int(const.TELLSTICK_STOP):
            logging.debug('[DEVICE] Sending command STOP to device id {}'.format(id))
            cmd_status = d.stop(id)

        if not cmd_status:
            logging.debug('[DEVICE] Command "{}" not supported, please open a github issue with this message.'.format(msg))

    client.subscribe('{}/+/+/set'.format(config['home_assistant']['state_topic']))
    client.on_message = on_message


def device_event(id_, method, data, cid):
    method_string = METHODS.get(method, 'UNKNOWN METHOD {0}'.format(method))
    string = '[DEVICE] {0} -> {1} ({2})'.format(id_, method_string, method)
    if method == const.TELLSTICK_DIM:
        string += ' [{0}]'.format(data)
    logging.debug('[DEVICE] {}'.format(string))

    # TODO: Need method to lookup id and get model, now assuming "switch"
    topic = d.create_topic(id_, 'switch')
    data = d.create_topic_data('switch', method)
    publish_mqtt(mqtt_client, topic, data)


def sensor_event(protocol, model, id_, dataType, value, timestamp, cid):
    type_string = TYPES.get(dataType, 'UNKNOWN METHOD {0}'.format(dataType))
    string = '[SENSOR] {0} {1} ({2}) = {3}'.format(id_, model, type_string, value)
    logging.debug('[SENSOR] {}'.format(string))

    topic = s.create_topic(id_, type_string)
    data = s.create_topic_data(type_string, value)
    publish_mqtt(mqtt_client, topic, data)


def initial_publish(mqtt_client, topics):
    for topic in topics:
        if 'config' in topic:
            publish_mqtt(mqtt_client, topic['config']['topic'], topic['config']['data'])
        if 'state' in topic:
            publish_mqtt(mqtt_client, topic['state']['topic'], topic['state']['data'])
        if 'command' in topic:
            if 'data' in topic['command']:
                publish_mqtt(mqtt_client, topic['command']['topic'], topic['command']['data'])



with open('./logging.yaml', 'r') as stream:
    logging_config = yaml.load(stream, Loader=yaml.FullLoader)

logging.config.dictConfig(logging_config)
logger = logging.getLogger('telldus-core-mqtt-main')

# Setup connection MQTT server
c = telldus.Telldus()
config = c.get_config
client_id = 'telldus-core-mqtt-{}'.format(random.randint(0, 1000))
mqtt_client = connect_mqtt(config, client_id)

# Initialize event listener for telldus-core
telldus_core = asyncio.get_event_loop()
dispatcher = td.AsyncioCallbackDispatcher(telldus_core)
core = td.TelldusCore(callback_dispatcher=dispatcher)
callbacks = []

# Events to listen for from telldus-core
callbacks.append(core.register_device_event(device_event))
callbacks.append(core.register_sensor_event(sensor_event))

# On program start, collect sensors to publish to MQTT server
s = telldus.Sensor()
sensor_topics = s.create_topics(s.get())
initial_publish(mqtt_client, sensor_topics)

# On program start, collect devices to publish to MQTT server
d = telldus.Device()
device_topics = d.create_topics(d.get())
initial_publish(mqtt_client, device_topics)

# Main loop
try:
    subscribe_device(mqtt_client)
    mqtt_client.loop_start()
    telldus_core.run_forever()
except KeyboardInterrupt:
    mqtt_client.unsubscribe('{}/+/+/set'.format(config['home_assistant']['state_topic']))
    mqtt_client.disconnect()