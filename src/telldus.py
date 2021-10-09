#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import yaml
import logging

import tellcore.telldus as td
import tellcore.constants as const

from pyaml_env import parse_config


with open('./logging.yaml', 'r') as stream:
    logging_config = yaml.load(stream, Loader=yaml.FullLoader)

logging.config.dictConfig(logging_config)
logger = logging.getLogger('telldus-core-mqtt')


class Telldus:
    def __init__(self):
        self.core = td.TelldusCore()
        self.config = parse_config('config_default.yaml')

    @property
    def get_config(self):
        return self.config

    # @name.setter
    # def name(self, name):
    #     self.__name = name


    def create_topics(self, data):
        topics_to_create = []
        for d in data:
            topics = {}
            topics['config'] = {}
            topics['state'] = {}
            if 'sensor' in d:
                topics['config']['topic'] = '{}/sensor/{}_telldus/{}/config'.format(self.config['home_assistant']['config_topic'], d['sensor'].id, d['type'])
                topics['state']['topic'] = '{}/{}/{}/state'.format(self.config['home_assistant']['state_topic'], d['sensor'].id, d['type'])
                config_data = self._create_config_data(d['sensor'], topics['state']['topic'], d)
            elif 'device' in d:
                topics['config']['topic'] = '{}/{}/{}_telldus/{}/config'.format(self.config['home_assistant']['config_topic'], d['type'], d['device'].id, d['type'])
                topics['state']['topic'] = '{}/{}/{}/state'.format(self.config['home_assistant']['state_topic'], d['device'].id, d['type'])
                topics['command'] = {}
                topics['command']['topic'] = '{}/{}/{}/set'.format(self.config['home_assistant']['state_topic'], d['device'].id, d['type'])
                config_data = self._create_config_data(d['device'], topics['state']['topic'], d, topics['command']['topic'])

            topics['config']['data'] = json.dumps(config_data, ensure_ascii=False)
            topics['state']['data'] = json.dumps(d['state_data'], ensure_ascii=False)
            topics_to_create.append(topics)

        return topics_to_create


    def _create_config_data(self, device, state_topic, extra, command_topic=None):
        # common
        config_data = {}
        config_data['unique_id'] = '{}_telldus_{}'.format(device.id, extra['type'])
        if hasattr(device, 'name'):
            config_data['name'] = device.name
        else:
            config_data['name'] = 'telldus_{}_{}'.format(device.id, extra['type'])
        config_data['state_topic'] = state_topic
        config_data['value_template'] = '{{ value_json.%s }}' % extra['type']
        config_data['device'] = {}
        config_data['device']['identifiers'] = []
        config_data['device']['identifiers'].append('{}_{}'.format(device.id, device.model))
        if hasattr(device, 'name'):
            config_data['device']['name'] = device.name
        else:
            config_data['device']['name'] = '{}_{}'.format(device.id, device.model)
        config_data['device']['model'] = device.model
        config_data['device']['manufacturer'] = device.protocol
        # sensor only
        # if unit is set assume sensor
        if 'unit' in extra:
            config_data['device_class'] = extra['type']
            config_data['unit_of_measurement'] = extra['unit']
        # device only
        # if command_topic exists assume device
        if command_topic != None:
            config_data['command_topic'] = command_topic
            config_data['payload_on'] = const.TELLSTICK_TURNON
            config_data['payload_off'] = const.TELLSTICK_TURNOFF
            config_data['state_on'] = const.TELLSTICK_TURNON
            config_data['state_off'] = const.TELLSTICK_TURNOFF

        return config_data


    def create_topic(self, id, model):
        topic = '{}/{}/{}/state'.format(self.config['home_assistant']['state_topic'], id, model)
        return topic


    def create_topic_data(self, type_string, value):
        data = { type_string: value }
        return json.dumps(data, ensure_ascii=False)


class Sensor(Telldus):
    def get(self):
        sensors_data = []
        wind_directions = ["N", "NNE", "NE", "ENE",
                           "E", "ESE", "SE", "SSE",
                           "S", "SSW", "SW", "WSW",
                           "W", "WNW", "NW", "NNW"]

        for sensor in self.core.sensors():
            if sensor.has_temperature():
                s = {}
                state_data = {}
                state_data['temperature'] = sensor.temperature().value
                s['type'] = 'temperature'
                s['unit'] = u'°C'
                s['sensor'] = sensor
                s['state_data'] = state_data
                sensors_data.append(dict(s))

            if sensor.has_humidity():
                s = {}
                state_data = {}
                state_data['humidity'] = sensor.humidity().value
                s['type'] = 'humidity'
                s['unit'] = '%'
                s['sensor'] = sensor
                s['state_data'] = state_data
                sensors_data.append(dict(s))

            if sensor.has_rainrate():
                s = {}
                state_data = {}
                state_data['rainrate'] = sensor.rainrate().value
                s['type'] = 'rainrate'
                s['unit'] = 'mm/h'
                s['sensor'] = sensor
                s['state_data'] = state_data
                sensors_data.append(dict(s))

            if sensor.has_raintotal():
                s = {}
                state_data = {}
                state_data['raintotal'] = sensor.raintotal().value
                s['type'] = 'raintotal'
                s['unit'] = 'mm'
                s['sensor'] = sensor
                s['state_data'] = state_data
                sensors_data.append(dict(s))

            if sensor.has_winddirection():
                s = {}
                state_data = {}
                state_data['winddirection'] = int(float(sensor.winddirection().value / 22.5))
                s['type'] = 'winddirection'
                s['unit'] = wind_directions[int(float(sensor.winddirection().value) / 22.5)]
                s['sensor'] = sensor
                s['state_data'] = state_data
                sensors_data.append(dict(s))

            if sensor.has_windaverage():
                s = {}
                state_data = {}
                state_data['windaverage'] = sensor.windaverage().value
                s['type'] = 'windaverage'
                s['unit'] = 'm/s'
                s['sensor'] = sensor
                s['state_data'] = state_data
                sensors_data.append(dict(s))

            if sensor.has_windgust():
                s = {}
                state_data = {}
                state_data['windgust'] = sensor.windgust().value
                s['type'] = 'windgust'
                s['unit'] = 'm/s'
                s['sensor'] = sensor
                s['state_data'] = state_data
                sensors_data.append(dict(s))

        return sensors_data


class Device(Telldus):
    def get(self, id=None):
        devices_data = []

        if not id:
            devices = self.core.devices()
        else:
            devices = [self._find_device(id)]

        for device in devices:
            d = {}
            device_model = ''

            if 'switch' in device.model:
                device_model = 'switch'

            if 'dimmer' in device.model:
                device_model = 'dimmer'

            if device_model == '':
                logging.INFO('Device "{}" not yet supported, please raise an github issue.'.format(device.model))
                continue

            state_data = {}

            state_data[device_model] = device.last_sent_command(
                                const.TELLSTICK_TURNON
                                | const.TELLSTICK_TURNOFF
                                | const.TELLSTICK_DIM)

            d['type'] = device_model
            d['device'] = device
            d['state_data'] = state_data

            devices_data.append(dict(d))

        return devices_data


    def turn_on(self, id):
        device = self._find_device(id)
        if device is not None:
            for _i in range(int(self.config['telldus']['repeat_cmd'])):
                time.sleep(1)
                device.turn_on()
            return True
        return False


    def turn_off(self, id):
        device = self._find_device(id)
        if device is not None:
            for _i in range(int(self.config['telldus']['repeat_cmd'])):
                time.sleep(1)
                device.turn_off()
            return True
        return False


    def bell(self, id):
        device = self._find_device(id)
        if device is not None:
            for _i in range(int(self.config['telldus']['repeat_cmd'])):
                time.sleep(1)
                device.bell()
            return True
        return False


    def dim(self, id, value):
        if int(value) >= 0 and int(value) <= 255:
            device = self._find_device(id)
            if device is not None:
                for _i in range(int(self.config['telldus']['repeat_cmd'])):
                    time.sleep(1)
                    device.dim(int(value))
                return True

        logging.warning('Dim value "{}" not in range 0 - 255'.format(value))
        return False


    def execute(self, id):
        device = self._find_device(id)
        if device is not None:
            for _i in range(int(self.config['telldus']['repeat_cmd'])):
                time.sleep(1)
                device.execute()
            return True
        return False


    def up(self, id):
        device = self._find_device(id)
        if device is not None:
            for _i in range(int(self.config['telldus']['repeat_cmd'])):
                time.sleep(1)
                device.up()
            return True
        return False


    def down(self, id):
        device = self._find_device(id)
        if device is not None:
            for _i in range(int(self.config['telldus']['repeat_cmd'])):
                time.sleep(1)
                device.down()
            return True
        return False


    def stop(self, id):
        device = self._find_device(id)
        if device is not None:
            for _i in range(int(self.config['telldus']['repeat_cmd'])):
                time.sleep(1)
                device.stop()
            return True
        return False


    def _find_device(self, device):
        for d in self.core.devices():
            if str(d.id) == device or d.name == device:
                return d
        logging.warning("Device '{}' not found".format(device))
        return None