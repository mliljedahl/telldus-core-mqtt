# Build

## dockerhub

```
$ docker build -t telldus-core-mqtt:latest -t mliljedahl/telldus-core-mqtt:latest -t mliljedahl/telldus-core-mqtt:1.0.0 .
$ docker login
$ docker push mliljedahl/telldus-core-mqtt
```

## github

```
$ docker build -t telldus-core-mqtt:latest -t ghcr.io/mliljedahl/telldus-core-mqtt:latest -t ghcr.io/mliljedahl/telldus-core-mqtt:1.0.0 .
$ docker login ghcr.io
$ docker push ghcr.io/mliljedahl/telldus-core-mqtt
```