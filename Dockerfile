FROM python:3.4.3
MAINTAINER Visio Box <root@visiobox.ru>

RUN apt-get update && apt-get install -y \
    openssl \
    tor \
    git \
    mercurial \
    subversion \
    golang

ADD . /project
WORKDIR /project

RUN pip install -r config/requirements.txt

ENV PATH /go/bin:/usr/local/go/bin:$PATH
ENV GOPATH /go

RUN mkdir -p /go && chmod -R 777 /go

RUN go get github.com/cespare/reflex

#EXPOSE 8080
#CMD python -W ignore manage.py runserver 0.0.0.0:8080
