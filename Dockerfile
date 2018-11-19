FROM python:3-alpine

MAINTAINER fireinice <fireinice@gmail.com>

WORKDIR /app

ADD . /app

ENTRYPOINT ["python", "ddns.py"]
