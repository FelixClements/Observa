FROM python:3.12-slim

LABEL maintainer="Tautulli"

ARG BRANCH
ARG COMMIT

ENV TAUTULLI_DOCKER=True
ENV TZ=UTC

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    findutils \
    git \
    gosu \
    passwd \
    tzdata \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app
RUN \
  groupadd -g 1000 tautulli && \
  useradd -u 1000 -g 1000 tautulli && \
  echo ${BRANCH} > /app/branch.txt && \
  echo ${COMMIT} > /app/version.txt

RUN \
  mkdir /config && \
  touch /config/DOCKER
VOLUME /config

CMD [ "python", "Tautulli.py", "--datadir", "/config" ]
ENTRYPOINT [ "./start.sh" ]

EXPOSE 8181
HEALTHCHECK --start-period=90s CMD curl -ILfks https://localhost:8181/status > /dev/null || curl -ILfs http://localhost:8181/status > /dev/null || exit 1
