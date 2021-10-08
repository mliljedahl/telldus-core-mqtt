# telldus-core-mqtt

**telldus-core-mqtt** is a MQTT broker for telldus-core to integrate with [Home Assistant](https://www.home-assistant.io/) using their [MQTT Discovery](https://www.home-assistant.io/docs/mqtt/discovery/).

For now sensors and on/off switches are supported, see [Known limitations](#Known-limitations) and [Development](#Development) for more information.

## Configuration

It is possible to either use the `config_default.yaml` file or set the config parameters found in the file as environment variables. If the environment variables are not found the values from `config_default.yaml` are used.

## Installation

Best option is to run the `docker-compose.yaml` file. Else install it along side `telldus-core` in a python virtual environment, required packages are found in `requirements.txt`.

### Docker Compose

```
$ docker-compose up -d
```

### Python virtual environment

```
$ python3 -m venv venv
$ source venv/bin/activate
$ pip3 install --no-cache-dir -r requirements.txt
$ ./main.py
```

## Known limitations

The following are the known limitations.

* telldus-core do not compile in alpine linux 3.14.
* The only sensors that have been tested are the temperature and humidity sensors. As for devices only on/off switches have been tested.
* Tested with a TellStick Duo, might also work with the TellStick or other controllers supported by telldus-core.
* Tests are missing.

## Development

For now the only sensors that have been tested are the temperature and humidity sensors. As for devices only on/off switches have been tested. So there is still much to test and develop in this project. Please file an [issue](https://github.com/mliljedahl/telldus-core-mqtt/issues) or even better, provide a [pull request](https://github.com/mliljedahl/telldus-core-mqtt/pulls).

If you want to provide me with sensors or devices for testing and further development that is also welcome.

### Cloning the repo

To build the Docker image all submodules needs to be fetched as well.

```
$ git clone git@github.com:mliljedahl/telldus-core-mqtt.git
$ cd telldus-core-mqtt
$ git submodule update --init
```

### Building the Docker image

```
$ docker build -t telldus-core-mqtt .
```

### Debugging the Docker image

```
$ docker run --rm -v ./tellstick.conf:/etc/tellstick.conf:ro --device=/dev/bus/usb:/dev/bus/usb:rwm -it telldus-core-mqtt:latest sh
$ docker logs -f telldus-core-mqtt
```

### Docker Compose

In the `dev` folder there is a development docker-compose file that brings up both mosquitto and home-assistant.
```
$ docker-compose up -d
```

#### MQTT User

To set a password the first time, start the container using the docker-compose.yaml development file and enter the mosquitto container.
```
$ docker exec -it mosquitto sh
$ mosquitto_passwd -c /mosquitto/config/mosquitto.passwd telldus-core-mqtt
```

## Reporting bugs

Please report bugs in the [issue tracker](https://github.com/mliljedahl/telldus-core-mqtt/issues).

## License

Distributed under the Apache 2.0 License. See [LICENSE](https://github.com/mliljedahl/telldus-core-mqtt/blob/master/LICENSE) for more information.