FROM docker.io/library/python:3.12

WORKDIR /work
ENV PRE_COMMIT_HOME .cache/pre-commit

RUN apt-get update -y \
 && apt-get install gnupg2 libegl1-mesa libgl1 libxkbcommon-x11-0 libdbus-1-3 qtwayland5 -y

# install poetry
RUN pip install poetry
# install vscode-task-runner
RUN pip install vscode-task-runner