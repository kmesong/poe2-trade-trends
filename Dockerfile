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

# Install backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy built frontend assets from Stage 1 to where Flask expects them
# We configured Flask to look in ../poe2-trends/dist
COPY --from=build-frontend /app/frontend/dist /app/poe2-trends/dist

# Expose port 5000
EXPOSE 5000

# Define environment variables
ENV FLASK_APP=server.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run Flask
CMD ["flask", "run"]
