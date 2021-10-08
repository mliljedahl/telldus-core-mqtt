# Build

[Good article](https://medium.com/@artur.klauser/building-multi-architecture-docker-images-with-buildx-27d80f7e2408) about multi arc builds.

## dockerhub

```
$ docker buildx build --push --platform linux/arm/v6,linux/arm/v7,linux/arm64/v8,linux/amd64,linux/386 -t mliljedahl/telldus-core-mqtt:latest -t mliljedahl/telldus-core-mqtt:1.0.0 .
$ docker build -t telldus-core-mqtt:latest -t mliljedahl/telldus-core-mqtt:latest -t mliljedahl/telldus-core-mqtt:1.0.0 .
$ docker login
$ docker push mliljedahl/telldus-core-mqtt
```

## github

```
$ docker buildx build --push --platform linux/arm/v6,linux/arm/v7,linux/arm64/v8,linux/amd64,linux/386 -t ghcr.io/mliljedahl/telldus-core-mqtt:latest -t ghcr.io/mliljedahl/telldus-core-mqtt:1.0.0 .
$ docker build -t telldus-core-mqtt:latest -t ghcr.io/mliljedahl/telldus-core-mqtt:latest -t ghcr.io/mliljedahl/telldus-core-mqtt:1.0.0 .
$ docker login ghcr.io
$ docker push ghcr.io/mliljedahl/telldus-core-mqtt
```