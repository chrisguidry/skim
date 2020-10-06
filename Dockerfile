FROM python:3.8-slim
LABEL maintainer="chris@theguidrys.us"

VOLUME /feeds/

RUN mkdir -p /skim/
WORKDIR /skim/

COPY requirements.txt /skim/
RUN pip install -r /skim/requirements.txt

COPY . /skim/

ENTRYPOINT ["/usr/local/bin/python"]
CMD ["-m", "skim"]
