FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Prevent Python from generating cache files
ENV PYTHONDONTWRITEBYTECODE=1

# Display logs immediately
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create the instance directory for SQLite
RUN mkdir -p /app/instance

# Expose Flask application port
EXPOSE 5000

# Start Attendify
CMD ["python", "run.py"]
