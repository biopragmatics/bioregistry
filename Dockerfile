FROM python:3.11-alpine

RUN python -m pip install --upgrade pip
RUN python -m pip install --upgrade wheel
RUN python -m pip install bioregistry[web]
ENTRYPOINT python -m bioregistry web --port 8766 --host "0.0.0.0" --workers 4
