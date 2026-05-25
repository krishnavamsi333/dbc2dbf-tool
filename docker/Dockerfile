FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/ ./backend/

# Copy frontend (served as static files via Flask or nginx)
COPY frontend/ ./frontend/

# Expose port
EXPOSE 5000

# Set environment
ENV FLASK_DEBUG=false
ENV PORT=5000
ENV PYTHONPATH=/app/backend

# Run the Flask app
CMD ["python", "backend/app.py"]