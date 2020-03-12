FROM python:3.7-alpine
RUN apk update && apk add build-base
WORKDIR /app
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD [ "python", "/app/main.py" ]