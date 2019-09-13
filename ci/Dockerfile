FROM debian:buster as buster
RUN apt-get update -y && apt-get install python3 -y --fix-missing
RUN apt-get install sudo -y
RUN apt-get install python3-setuptools -y --fix-missing
RUN apt-get install python3-pytest -y --fix-missing
RUN apt-get install git -y --fix-missing
ARG TAG=${TRAVIS_TAG}
COPY python3-gar_${TAG}_all.deb python3-gar_${TAG}_all.deb
RUN apt-get install ./python3-gar_${TAG}_all.deb -y
RUN git clone https://github.com/suvarchal/gar
WORKDIR ./gar
RUN git checkout v${TAG}
RUN py.test-3

FROM debian:bullseye as bullseye
RUN apt-get update -y && apt-get install python3 -y 
RUN apt-get install sudo -y
RUN apt-get install python3-setuptools -y 
RUN apt-get install python3-pytest -y 
RUN apt-get install git -y --fix-missing
ARG TAG=${TRAVIS_TAG}
COPY python3-gar_${TAG}_all.deb python3-gar_${TAG}_all.deb
RUN apt-get install ./python3-gar_${TAG}_all.deb -y
RUN git clone https://github.com/suvarchal/gar
WORKDIR ./gar
RUN git checkout v${TAG}
RUN py.test-3

FROM ubuntu:bionic as bionic
RUN apt-get update -y && apt-get install python3 -y 
RUN apt-get install sudo -y
RUN apt-get install python3-setuptools -y 
RUN apt-get install python3-pytest -y 
RUN apt-get install git -y --fix-missing
ARG TAG=${TRAVIS_TAG}
COPY python3-gar_${TAG}_all.deb python3-gar_${TAG}_all.deb
RUN apt-get install ./python3-gar_${TAG}_all.deb -y
RUN git clone https://github.com/suvarchal/gar
WORKDIR ./gar
RUN git checkout v${TAG}
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
RUN py.test-3
