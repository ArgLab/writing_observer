FROM python:3.10
RUN git config --global --add safe.directory /app
WORKDIR /app

# Future work:
# - This image currently uses an older Python base image version.
# - Update the Python version to align with current LO/WO support targets.
# - Some configurations may also require extra roster files mounted/provided
#   at runtime (for example: admins.yaml or teachers.yaml).
# - Consider a layered setup:
#   1) maintain a shared "base LO" Docker image
#   2) extend it with a WO-specific image (or other module-set images)

# TODO start redis in here
# see about docker loopback
RUN apt-get update && \
    apt-get install -y python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . /app

RUN make install
CMD ["make", "run"]
