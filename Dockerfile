FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything
COPY . .

ENV PORT=7860
ENV PYTHONPATH=/app/backend

EXPOSE 7860

CMD ["python", "backend/app.py"]