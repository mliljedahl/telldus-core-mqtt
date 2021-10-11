#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import random
import asyncio
import logging.config
import yaml

from paho.mqtt import client as mqtt_client

import src.telldus as telldus
from src.telldus import const, td


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


def connect_mqtt(config) -> mqtt_client:
    def on_connect(client, userdata, flags, return_code):
        # pylint: disable=unused-argument
        if return_code == 0:
            logging.info('Connected to MQTT Broker!')
        else:
            logging.critical('Failed to connect, return code %d', return_code)

    client = mqtt_client.Client(CLIENT_ID)
    client.username_pw_set(config['mqtt']['user'], config['mqtt']['pass'])
    client.on_connect = on_connect
    client.connect(config['mqtt']['broker'], int(config['mqtt']['port']))

    return client


def publish_mqtt(client, topic, msg):
    time.sleep(1)

    result = client.publish(topic, msg, retain=True)

    if result[0] == 0:
        logging.info('Send "%s" to topic "%s"', msg, topic)
    else:
        logging.error('Failed to send message to topic "%s"', topic)


def subscribe_device(client: mqtt_client):
    def on_message(client, userdata, msg):
        # pylint: disable=unused-argument
        logging.info('Received "%s" from "%s" topic', msg.payload.decode(),
                                                      msg.topic)
        device_id = msg.topic.split('/')[1]
        module = msg.topic.split('/')[2]
        action = msg.topic.split('/')[3]
        cmd_status = False

        if module == 'light':
            if action == 'dim':
                logging.debug('[DEVICE] Sending command DIM "%d" to device '
                              'id %d', msg.payload.decode(), device_id)
                cmd_status = d.dim(device_id, int(msg.payload.decode()))

        if action != 'dim':
            if int(msg.payload.decode()) == int(const.TELLSTICK_TURNON):
                logging.debug('[DEVICE] Sending command ON to device '
                              'id %d', device_id)
                cmd_status = d.turn_on(device_id)

            if int(msg.payload.decode()) == int(const.TELLSTICK_TURNOFF):
                logging.debug('[DEVICE] Sending command OFF to device '
                              'id %d', device_id)
                cmd_status = d.turn_off(device_id)

        if int(msg.payload.decode()) == int(const.TELLSTICK_BELL):
            logging.debug('[DEVICE] Sending command BELL to device '
                          'id %d', device_id)
            cmd_status = d.bell(device_id)

        if int(msg.payload.decode()) == int(const.TELLSTICK_EXECUTE):
            logging.debug('[DEVICE] Sending command EXECUTE to device '
                          'id %d', device_id)
            cmd_status = d.execute(device_id)

        if int(msg.payload.decode()) == int(const.TELLSTICK_UP):
            logging.debug('[DEVICE] Sending command UP to device id %d', device_id)
            cmd_status = d.up(device_id)

        if int(msg.payload.decode()) == int(const.TELLSTICK_DOWN):
            logging.debug('[DEVICE] Sending command DOWN to device id %d', device_id)
            cmd_status = d.down(device_id)

        if int(msg.payload.decode()) == int(const.TELLSTICK_STOP):
            logging.debug('[DEVICE] Sending command STOP to device id %d', device_id)
            cmd_status = d.stop(device_id)

        if not cmd_status:
            logging.debug('[DEVICE] Command "%s" not supported, please open'
                          ' a github issue with this message.', msg)

    client.subscribe('{}/+/+/set'.format(
        config['home_assistant']['state_topic']))
    client.on_message = on_message


def device_event(id_, method, data, cid):
    # pylint: disable=unused-argument
    method_string = METHODS.get(method, 'UNKNOWN METHOD {0}'.format(method))
    string = '[DEVICE] {0} -> {1} ({2})'.format(id_, method_string, method)
    if method == const.TELLSTICK_DIM:
        string += ' [{0}]'.format(data)
    logging.debug(string)

    if method == const.TELLSTICK_DIM:
        topic = d.create_topic(id_, 'light')
        topic_data = d.create_topic_data('light', data)
    else:
        topic = d.create_topic(id_, 'switch')
        topic_data = d.create_topic_data('switch', method)
    publish_mqtt(mqtt_client, topic, topic_data)


def sensor_event(protocol, model, id_, data_type, value, timestamp, cid):
    # pylint: disable=unused-argument
    type_string = TYPES.get(data_type, 'UNKNOWN METHOD {0}'.format(data_type))
    string = '[SENSOR] {0} {1} ({2}) = {3}'.format(
        id_, model, type_string, value)
    logging.debug(string)

    # Sensors can be added or discovered in telldus-core without
    # a restart, ensure config topic for HASS
    sensor_topics = s.create_topics(s.get(id_))
    initial_publish(mqtt_client, sensor_topics)

    topic = s.create_topic(id_, type_string)
    data = s.create_topic_data(type_string, value)
    publish_mqtt(mqtt_client, topic, data)


def initial_publish(mqtt_client, topics):
    for topic in topics:
        if 'config' in topic:
            publish_mqtt(mqtt_client, topic['config']['topic'],
                         topic['config']['data'])
        if 'state' in topic:
            publish_mqtt(mqtt_client, topic['state']['topic'],
                         topic['state']['data'])


with open('./logging.yaml', 'r', encoding='utf-8') as stream:
    logging_config = yaml.load(stream, Loader=yaml.FullLoader)

logging.config.dictConfig(logging_config)
logger = logging.getLogger('telldus-core-mqtt-main')

# Wait 5s for telldus-core to start and start collecting data
logging.info('Waiting for telldus-core to start...')
time.sleep(5)
logging.info('telldus-core have started.')

# Setup connection MQTT server
c = telldus.Telldus()
config = c.get_config
CLIENT_ID = 'telldus-core-mqtt-{}'.format(random.randint(0, 1000))
mqtt_client = connect_mqtt(config)

# On program start, collect sensors to publish to MQTT server
s = telldus.Sensor(c.td_core)
sensors_topics = s.create_topics(s.get())
initial_publish(mqtt_client, sensors_topics)

# On program start, collect devices to publish to MQTT server
d = telldus.Device(c.td_core)
devices_topics = d.create_topics(d.get())
initial_publish(mqtt_client, devices_topics)

# Initialize event listener for telldus-core
telldus_core = asyncio.get_event_loop()
dispatcher = td.AsyncioCallbackDispatcher(telldus_core)
core = td.TelldusCore(callback_dispatcher=dispatcher)
callbacks = []

# Events to listen for from telldus-core
callbacks.append(core.register_device_event(device_event))
callbacks.append(core.register_sensor_event(sensor_event))

# Main loop
try:
    subscribe_device(mqtt_client)
    mqtt_client.loop_start()
    telldus_core.run_forever()
except KeyboardInterrupt:
    mqtt_client.unsubscribe('{}/+/+/set'.format(
        config['home_assistant']['state_topic']))
    mqtt_client.disconnect()
