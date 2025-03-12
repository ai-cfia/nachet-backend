FROM python:3.11-bullseye

WORKDIR /app

ENV QUART_APP=app.py
ENV QUART_ENV=development
ENV PYTHONUNBUFFERED True
ENV PYTHONPATH=/app

COPY ./requirements2025031201.txt .

RUN pip install --no-cache-dir -r requirements2025031201.txt

COPY . ./

CMD hypercorn -b :$PORT app:app
