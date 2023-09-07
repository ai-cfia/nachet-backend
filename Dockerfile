FROM python:3

WORKDIR /app

ENV QUART_APP=app.py
ENV QUART_ENV=development
ENV PYTHONUNBUFFERED True
ENV PYTHONPATH=/app

COPY ./requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . ./

CMD hypercorn -b :8080 app:app
