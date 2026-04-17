FROM python:3.9-slim

WORKDIR /app

COPY ./app /app

RUN pip3 install --no-cache-dir -r requirements.txt

# Moved so packages can be installed without permission issues
RUN useradd -m -u 1000 nonroot 

USER nonroot

EXPOSE 5070

CMD ["python3", "main.py"]
