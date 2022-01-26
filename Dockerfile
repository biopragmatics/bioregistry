FROM python:3.10-alpine

RUN python -m pip install --upgrade pip
RUN python -m pip install gunicorn
WORKDIR /app
COPY . /app
RUN python -m pip install .[web]
WORKDIR /
RUN rm -rf /app
ENTRYPOINT python -m bioregistry web --port 8766 --host "0.0.0.0" --with-gunicorn --workers 4
