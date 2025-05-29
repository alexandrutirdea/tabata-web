FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && apt-get clean

COPY tabata-web.py .

COPY config.yaml .

COPY tabata.sh .

COPY ./static /app/static

COPY workoutmusic.py .

RUN pip install flask pyyaml plexapi

EXPOSE 5011

CMD ["python3", "tabata-web.py"]
