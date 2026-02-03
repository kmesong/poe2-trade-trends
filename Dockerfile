# Stage 1: Build the React application
FROM node:18-alpine as build-frontend

WORKDIR /app/frontend

COPY poe2-trends/package*.json ./
RUN npm install

COPY poe2-trends/ .
RUN npm run build

# Stage 2: Set up Python backend and serve frontend
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/

COPY --from=build-frontend /app/frontend/dist /poe2-trends/dist

EXPOSE 5000

ENV FLASK_APP=server.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

ENV PYTHONPATH=/app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "backend.server:app"]
