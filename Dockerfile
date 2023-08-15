FROM python:3

WORKDIR /app

ENV QUART_APP=app.py
ENV QUART_ENV=development

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["hypercorn", "app:app", "--reload"]
