FROM python:3.9
LABEL maintainer="chris@theguidrys.us"

VOLUME /feeds/

RUN mkdir -p /skim/
WORKDIR /skim/

RUN apt update && \
    apt install -y sqlite3 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /skim/
RUN pip install -r /skim/requirements.txt

COPY . /skim/

ENTRYPOINT ["/usr/local/bin/python", "-m"]
CMD ["skim"]
