FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Set environment variables
ENV AWS_DEFAULT_REGION=us-east-1
ENV AWS_ENDPOINT_URL=http://host.docker.internal:4566
ENV AWS_ACCESS_KEY_ID=test
ENV AWS_SECRET_ACCESS_KEY=test
ENV PORT=8080

# Run the application
CMD ["python", "app.py"]
