FROM python:3.10
RUN git config --global --add safe.directory /app
WORKDIR /app

# TODO start redis in here
# see about docker loopback
RUN apt-get update && \
    apt-get install -y python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . /app

RUN make install
CMD ["make", "run"]
