FROM python:3.9
LABEL maintainer="chris@theguidrys.us"

RUN apt-get update && \
    apt-get install -y sqlite3 && \
    rm -rf /var/lib/apt/lists/*

ADD https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py /tmp/install-poetry.py
ENV PATH $PATH:/root/.local/bin
RUN python3 /tmp/install-poetry.py
RUN poetry config virtualenvs.create false

VOLUME /feeds/

RUN mkdir -p /skim/
WORKDIR /skim/

COPY poetry.lock pyproject.toml /skim/
RUN poetry install

COPY . /skim/

ENTRYPOINT ["/usr/local/bin/python", "-m"]
CMD ["skim"]
