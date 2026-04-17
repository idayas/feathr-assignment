FROM python:3.9-slim

RUN useradd -m -u 1000 nonroot 

USER nonroot

WORKDIR /app

COPY ./app /app

RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 5070

CMD ["python3", "main.py"]
# CMD ["sleep", "1000"]
