FROM cr.nthnv.me/docker.io/library/python:3.10

WORKDIR /work

RUN apt-get update -y \
 && apt-get install gnupg2 libeg11-mesa -y

COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock

RUN python -m pip install poetry \
 && python -m poetry install
