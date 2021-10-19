FROM python:3-alpine3.14

# Compile telldus-core source

WORKDIR /usr/src/

COPY telldus /usr/src/telldus

RUN apk add --no-cache \
      confuse \
      libftdi1 \
      libstdc++ \
      supervisor

RUN apk add --no-cache --virtual .build-dependencies \
      confuse-dev \
      cmake \
      gcc \
      g++ \
      libftdi1-dev \
      libtool \
      make \
      musl-dev \
    && cd telldus/telldus-core \
    && cmake . -DBUILD_LIBTELLDUS-CORE=ON -DBUILD_TDADMIN=OFF -DBUILD_TDTOOL=ON -DFORCE_COMPILE_FROM_TRUNK=ON \
    && make -j$(nproc) \
    && make \
    && make install \
    && apk del .build-dependencies \
    && rm -rf /usr/src/telldus

# telldus-core-mqtt

WORKDIR /usr/src/telldus-core-mqtt

COPY requirements.txt ./

RUN python -m pip install --upgrade pip \
    && pip3 install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1
RUN ln -s /usr/local/bin/tellcore_events /usr/bin/tdevents \
    && ln -s /usr/local/bin/tellcore_controllers /usr/bin/tdcontroller

COPY main.py ./
COPY config_default.yaml ./
COPY logging.yaml ./
COPY src ./src

# supervisord

COPY supervisord.conf /etc/supervisord.conf

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
