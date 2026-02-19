# Docker setup

## Docker

We also support spinning up a Docker container. First build the Docker image, then run it

```bash
docker build -t lo_workshop .   # build the root directory and tag it lo_workshop
docker run -it -p 8888:8888 lo_workshop      # -it attaches a terminal, -p attaches local port 8888 to dockers 8888 port
```

Note that building a docker image may take a few minutes.

## Docker Compose

Docker compose can manage both the normal Dockerfile and an instance of Redis. To both build and turn them on, run

```bash
docker compose up --build

# NOTE: older versions of docker use separate commands for
# building the images and turning them on
docker compose build
docker compose up
```

Watchdog will automatically re-run the command used to run application, `make run`. If we wish to develop while the Docker container is open, we need to modify the `run` command to re-install any packages when it restarts. Your local repository is being shared as a mount to the Docker container. Adding an install command makes sure that latest changes are used.

```Makefile
run:
    pip install -e learning_observer/
    cd learning_observer && python learning_observer --watchdog=restart
```

## Active development

We can add commands to re-install our local instances of the packages in Docker. This will allow us to do active development while the docker is running.

```Makefile
run:
    pip install -e learning_observer/
    pip install -e modules/learning_observer_template/
    cd learning_observer && python learning_observer --watchdog=restart
```
