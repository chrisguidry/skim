FROM python:3.9
LABEL maintainer="chris@theguidrys.us"

RUN DEBIAN_FRONTEND=noninteractive \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y \
        sqlite3 \
    && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt /skim/
RUN pip install -r /skim/requirements.txt

VOLUME /feeds/

RUN mkdir -p /skim/
WORKDIR /skim/
ENTRYPOINT ["/usr/local/bin/opentelemetry-instrument", "/usr/local/bin/python", "-m"]
CMD ["skim"]

COPY . /skim/
