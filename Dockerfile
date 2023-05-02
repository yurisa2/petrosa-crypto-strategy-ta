# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.10-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED=1

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN apt update && apt install -y git

# Install production dependencies.
RUN pip3 install --no-cache-dir -r requirements.txt

ENV NEW_RELIC_APP_NAME=petrosa-crypto-strategy-ta
ENV NEW_RELIC_DISTRIBUTED_TRACING_ENABLED=true
ENV NEW_RELIC_MONITOR_MODE=true
# ENV NEW_RELIC_LOG_LEVEL=debug
ENV NEW_RELIC_LOG=/tmp/newrelic.log

ENTRYPOINT ["newrelic-admin", "run-python", "main.py"]
