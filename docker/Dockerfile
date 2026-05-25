FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# HuggingFace Spaces runs on port 7860
ENV PORT=7860
ENV PYTHONPATH=/app/backend

EXPOSE 7860

CMD ["python", "backend/app.py"]