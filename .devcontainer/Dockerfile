FROM docker.io/library/python:3.10

WORKDIR /work

RUN apt-get update -y \
 && apt-get install gnupg2 libegl1-mesa libgl1 libxkbcommon-x11-0 libdbus-1-3 qtwayland5 -y

COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock

RUN python -m pip install poetry \
 && python -m poetry config virtualenvs.create false \
 && python -m poetry install
