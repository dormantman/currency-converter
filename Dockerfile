FROM python:3.6

ENV PYTHONUNBUFFERED 1

RUN mkdir /converter
WORKDIR /converter

RUN apt-get update && apt-get install -y \
    sudo && apt-get install -y \
    git

COPY . /converter/
