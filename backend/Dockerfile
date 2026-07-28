# Container build for the MajorMap AI API — used by Fly.io (`fly launch` from
# this directory), or any container host. Render/Railway don't need this; they
# use render.yaml / the root Procfile instead.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
# $PORT is injected by most PaaS hosts; default to 8000 locally.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
