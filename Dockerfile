# Stage 1: Build the React application
FROM node:18-alpine as build-frontend

WORKDIR /app/frontend

COPY poe2-trends/package*.json ./
RUN npm install

COPY poe2-trends/ .
RUN npm run build

# Stage 2: Set up Python backend and serve frontend
FROM python:3.9-slim

WORKDIR /app

# Copy requirements FIRST to leverage Docker cache
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code AFTER dependencies are installed
COPY backend/ .

# Copy built frontend assets from Stage 1 to where Flask expects them
# Flask static_folder is configured as '../poe2-trends/dist' relative to server.py
# Since server.py is at /app/server.py, Flask looks in /poe2-trends/dist
COPY --from=build-frontend /app/frontend/dist /poe2-trends/dist

# Copy instance folder for database
COPY --from=build-frontend /app/frontend/instance /app/instance

# Expose port 5000
EXPOSE 5000

# Define environment variables
ENV FLASK_APP=server.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Run Flask
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "server:app"]
