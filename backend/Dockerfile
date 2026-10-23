FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Migrate and seed, then start the server (see entrypoint.sh).
CMD ["sh", "entrypoint.sh"]
