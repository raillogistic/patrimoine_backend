FROM python:3.9 as builder

ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    libpq-dev  \
    build-essential python3-setuptools \
    python3-cffi libcairo2 libpango-1.0-0 \
    libpangocairo-1.0-0 libffi-dev \
    shared-mime-info   \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home
ADD ./requirements.txt .
RUN pip install -r requirements.txt

ADD ./entrypoint.sh .
RUN mkdir app

COPY /src/ /home/app/

FROM python:3.9 as app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 libpq-dev  \
    python3-dev  \
    gcc \
    git \
    libpangocairo-1.0-0 \
    build-essential python3-setuptools \
    python3-cffi  libpango-1.0-0 \
    libffi-dev \
    shared-mime-info   \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home

COPY --from=builder /home/requirements.txt .
COPY --from=builder /root/.cache /root/.cache

# Install app dependencies
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

COPY --from=builder home/app/ /home/app
COPY --from=builder home/entrypoint.sh /home
ENV PATH=/dcroot/.local/bin:$PATH


ENTRYPOINT ["./entrypoint.sh"]