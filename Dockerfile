FROM python:3.10-alpine

RUN python -m pip install --upgrade pip
RUN python -m pip install --upgrade wheel
RUN python -m pip install gunicorn bioregistry[web]
ENTRYPOINT python -m bioregistry web --port 8766 --host "0.0.0.0" --with-gunicorn --workers 4
