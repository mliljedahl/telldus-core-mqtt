#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import logging
import yaml

import tellcore.telldus as td
import tellcore.constants as const

from pyaml_env import parse_config


with open('./logging.yaml', 'r', encoding='utf-8') as stream:
    logging_config = yaml.load(stream, Loader=yaml.SafeLoader)

logging.config.dictConfig(logging_config)
logger = logging.getLogger('telldus-core-mqtt')


class Telldus:
    def __init__(self, core=None):
        self.config = parse_config('config_default.yaml')

        if core is None:
            self.core = td.TelldusCore()
        else:
            self.core = core

    @property
    def get_config(self):
        return self.config

    @property
    def td_core(self):
        return self.core

    def create_topics(self, data):
        config_topic = self.config['home_assistant']['config_topic']
        topics_to_create = []

        # pylint: disable=invalid-name
        for d in data:
            topics = {}
            topics['config'] = {}
            topics['state'] = {}
            if 'sensor' in d:
                topics['config']['topic'] = ('{}/sensor/{}_telldus/{}/config'
                                             .format(
                                                 config_topic,
                                                 d['sensor'].id, d['type']))
                topics['state']['topic'] = '{}/{}/{}/state'.format(
                    self.config['home_assistant']['state_topic'],
                    d['sensor'].id, d['type'])
                config_data = self._create_config_data(
                    d['sensor'], topics['state']['topic'], d)
            elif 'device' in d:
                topics['config']['topic'] = ('{}/{}/{}_telldus/{}/config'
                                             .format(
                                                 config_topic, d['type'],
                                                 d['device'].id, d['type']))
                topics['state']['topic'] = '{}/{}/{}/state'.format(
                    self.config['home_assistant']['state_topic'],
                    d['device'].id, d['type'])
                topics['command'] = {}
                topics['command']['topic'] = '{}/{}/{}/set'.format(
                    self.config['home_assistant']['state_topic'],
                    d['device'].id, d['type'])
                topics['brightness'] = {}
                topics['brightness']['command'] = '{}/{}/{}/set'.format(
                    self.config['home_assistant']['state_topic'],
                    d['device'].id, 'brightness')
                topics['brightness']['state'] = '{}/{}/{}/dim'.format(
                    self.config['home_assistant']['state_topic'],
                    d['device'].id, 'brightness')
                config_data = self._create_config_data(
                    d['device'], topics['state']['topic'], d,
                    topics['command']['topic'], topics['brightness'])

            topics['config']['data'] = json.dumps(
                config_data, ensure_ascii=False)
            topics['state']['data'] = json.dumps(
                d['state_data'], ensure_ascii=False)
            topics_to_create.append(topics)

        return topics_to_create

    def _create_config_data(self, device, state_topic, extra,
                            command_topic=None, bt_command=None):
        # common
        config_data = {}
        config_data['unique_id'] = ('{}_telldus_{}'
                                    .format(device.id, extra['type']))
        if hasattr(device, 'name'):
            config_data['name'] = device.name
        else:
            config_data['name'] = ('telldus_{}_{}'
                                   .format(device.id, extra['type']))
        if extra['type'] == 'light':
            bt_value_template = '{{ value_json.%s }}' % 'brightness'
            config_data['brightness_state_topic'] = bt_command['state']
            config_data['brightness_value_template'] = bt_value_template
            config_data['brightness_command_topic'] = bt_command['command']
        config_data['state_topic'] = state_topic
        config_data['value_template'] = '{{ value_json.%s }}' % extra['type']
        config_data['device'] = {}
        config_data['device']['identifiers'] = []
        config_data['device']['identifiers'].append('{}_{}'.format(
            device.id, device.model))
        if hasattr(device, 'name'):
            config_data['device']['name'] = device.name
        else:
            config_data['device']['name'] = '{}_{}'.format(
                device.id, device.model)
        config_data['device']['model'] = device.model
        config_data['device']['manufacturer'] = device.protocol
        # sensor only
        # if unit is set assume sensor
        if 'unit' in extra:
            config_data['device_class'] = extra['type']
            config_data['unit_of_measurement'] = extra['unit']
        # device only
        # if command_topic exists assume device
        if command_topic is not None:
            config_data['command_topic'] = command_topic
            config_data['payload_on'] = const.TELLSTICK_TURNON
            config_data['payload_off'] = const.TELLSTICK_TURNOFF
            if extra['type'] != 'light':
                config_data['state_on'] = const.TELLSTICK_TURNON
                config_data['state_off'] = const.TELLSTICK_TURNOFF

        return config_data

    def create_topic(self, type_id, model):
        if model == 'light':
            topic = '{}/{}/brightness/dim'.format(
                self.config['home_assistant']['state_topic'], type_id)
        else:
            topic = '{}/{}/{}/state'.format(
                self.config['home_assistant']['state_topic'], type_id, model)
        return topic

    def create_topic_data(self, type_string, value):
        data = {type_string: value}
        return json.dumps(data, ensure_ascii=False)


class Sensor(Telldus):
    def get(self, sensor_id=None):
        sensors_data = []
        wind_directions = ["N", "NNE", "NE", "ENE",
                           "E", "ESE", "SE", "SSE",
                           "S", "SSW", "SW", "WSW",
                           "W", "WNW", "NW", "NNW"]

        if sensor_id is not None:
            sensors = [self._find_sensor(sensor_id)]
        else:
            sensors = self.core.sensors()

        for sensor in sensors:
            if sensor.has_temperature():
                sensor_data = {}
                state_data = {}
                state_data['temperature'] = sensor.temperature().value
                sensor_data['type'] = 'temperature'
                sensor_data['unit'] = '°C'
                sensor_data['sensor'] = sensor
                sensor_data['state_data'] = state_data
                sensors_data.append(dict(sensor_data))

            if sensor.has_humidity():
                sensor_data = {}
                state_data = {}
                state_data['humidity'] = sensor.humidity().value
                sensor_data['type'] = 'humidity'
                sensor_data['unit'] = '%'
                sensor_data['sensor'] = sensor
                sensor_data['state_data'] = state_data
                sensors_data.append(dict(sensor_data))

            if sensor.has_rainrate():
                sensor_data = {}
                state_data = {}
                state_data['rainrate'] = sensor.rainrate().value
                sensor_data['type'] = 'rainrate'
                sensor_data['unit'] = 'mm/h'
                sensor_data['sensor'] = sensor
                sensor_data['state_data'] = state_data
                sensors_data.append(dict(sensor_data))

            if sensor.has_raintotal():
                sensor_data = {}
                state_data = {}
                state_data['raintotal'] = sensor.raintotal().value
                sensor_data['type'] = 'raintotal'
                sensor_data['unit'] = 'mm'
                sensor_data['sensor'] = sensor
                sensor_data['state_data'] = state_data
                sensors_data.append(dict(sensor_data))

            if sensor.has_winddirection():
                sensor_data = {}
                state_data = {}
                state_data['winddirection'] = int(float(
                    sensor.winddirection().value / 22.5))
                sensor_data['type'] = 'winddirection'
                sensor_data['unit'] = wind_directions[int(float(
                    sensor.winddirection().value) / 22.5)]
                sensor_data['sensor'] = sensor
                sensor_data['state_data'] = state_data
                sensors_data.append(dict(sensor_data))

            if sensor.has_windaverage():
                sensor_data = {}
                state_data = {}
                state_data['windaverage'] = sensor.windaverage().value
                sensor_data['type'] = 'windaverage'
                sensor_data['unit'] = 'm/s'
                sensor_data['sensor'] = sensor
                sensor_data['state_data'] = state_data
                sensors_data.append(dict(sensor_data))

            if sensor.has_windgust():
                sensor_data = {}
                state_data = {}
                state_data['windgust'] = sensor.windgust().value
                sensor_data['type'] = 'windgust'
                sensor_data['unit'] = 'm/s'
                sensor_data['sensor'] = sensor
                sensor_data['state_data'] = state_data
                sensors_data.append(dict(sensor_data))

        return sensors_data

    def _find_sensor(self, sensor_id):
        for sensor in self.core.sensors():
            if int(sensor.id) == int(sensor_id):
                return sensor
        logging.warning('Sensor id "%d" not found', int(sensor_id))
        return None


class Device(Telldus):
    def get(self, device_id=None):
        devices_data = []

        if device_id is not None:
            devices = [self._find_device(device_id)]
        else:
            devices = self.core.devices()

        for device in devices:
            device_data = {}
            device_model = ''

            if 'switch' in device.model:
                device_model = 'switch'

            if 'dimmer' in device.model:
                device_model = 'light'

            if device_model == '':
                logging.info('Device "%s" not yet supported, please raise '
                             'an github issue.', device.model)
                continue

            state_data = {}

            state_data[device_model] = device.last_sent_command(
                const.TELLSTICK_TURNON
                | const.TELLSTICK_TURNOFF
                | const.TELLSTICK_DIM)

            device_data['type'] = device_model
            device_data['device'] = device
            device_data['state_data'] = state_data

            devices_data.append(dict(device_data))

        return devices_data

    def turn_on(self, device_id):
        device = self._find_device(device_id)
        if device is not None:
            for _i in range(int(self.config['telldus']['repeat_cmd'])):
                time.sleep(1)
                device.turn_on()
            return True
        return False

    def turn_off(self, device_id):
        device = self._find_device(device_id)
        if device is not None:
            for _i in range(int(self.config['telldus']['repeat_cmd'])):
                time.sleep(1)
                device.turn_off()
            return True
        return False

    def bell(self, device_id):
        device = self._find_device(device_id)
        if device is not None:
            for _i in range(int(self.config['telldus']['repeat_cmd'])):
                time.sleep(1)
                device.bell()
            return True
        return False

    def dim(self, device_id, value):
        if int(value) >= 0 and int(value) <= 255:
            device = self._find_device(device_id)
            if device is not None:
                for _i in range(int(self.config['telldus']['repeat_cmd'])):
                    time.sleep(1)
                    device.dim(int(value))
                return True

        logging.warning('Dim value "%d" not in range 0 - 255', int(value))
        return False

    def execute(self, device_id):
        device = self._find_device(device_id)
        if device is not None:
            for _i in range(int(self.config['telldus']['repeat_cmd'])):
                time.sleep(1)
                device.execute()
            return True
        return False

    def up(self, device_id):
        # pylint: disable=invalid-name
        device = self._find_device(device_id)
        if device is not None:
            for _i in range(int(self.config['telldus']['repeat_cmd'])):
                time.sleep(1)
                device.up()
            return True
        return False

    def down(self, device_id):
        device = self._find_device(device_id)
        if device is not None:
            for _i in range(int(self.config['telldus']['repeat_cmd'])):
                time.sleep(1)
                device.down()
            return True
        return False

    def stop(self, device_id):
        device = self._find_device(device_id)
        if device is not None:
            for _i in range(int(self.config['telldus']['repeat_cmd'])):
                time.sleep(1)
                device.stop()
            return True
        return False

    def _find_device(self, device_id):
        for device in self.core.devices():
            if int(device.id) == int(device_id):
                return device
        logging.warning('Device id "%d" not found', int(device_id))
        return None
