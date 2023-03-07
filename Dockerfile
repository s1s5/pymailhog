FROM python:3.10.7-alpine3.16

COPY src /app/src
RUN adduser -D -u 1000 mailhog

USER mailhog
WORKDIR /pymailhog
CMD ["python", "/app/src/pymailhog.py"]

EXPOSE 1025 8025
