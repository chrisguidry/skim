FROM ubuntu:14.04
MAINTAINER chris@theguidrys.us

ENV DEBIAN_FRONTEND noninteractive
RUN echo 'deb http://us.archive.ubuntu.com/ubuntu/ trusty multiverse' >> /etc/apt/sources.list.d/multiverse.list && \
    apt-get update && \
    apt-get install -y \
        python3.4 \
        python3-pip \
        python3-gdbm \
        libxml2-dev \
        libxslt1-dev \
        zlib1g-dev \
        uwsgi \
        uwsgi-plugin-python3 \
    && rm -rf /var/lib/apt/lists/*

# extra tools that aren't install_requires of skim
RUN pip3 install ipython==2.4.1
RUN pip3 install tox==2.0.1

ADD . /skim
VOLUME /skim
WORKDIR /skim

VOLUME /storage

RUN pip3 install -e .

CMD /skim/webserver

# 3333: web, 4444: uwsgi
EXPOSE 3333 4444