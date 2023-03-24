# Local building/testing instructions:
# 1. docker build --tag bioregistry:dev .
# 2. docker run -p 8766:8766 bioregistry:dev
# 3. Navgiate in the web browser to http://localhost:8766

FROM python:3.11-alpine

RUN python -m pip install --upgrade pip
RUN python -m pip install --upgrade wheel
RUN python -m pip install bioregistry[web]
ENTRYPOINT python -m bioregistry web --port 8766 --host "0.0.0.0"
