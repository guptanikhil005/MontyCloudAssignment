#!/bin/bash

echo "Starting Instagram Image Service..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Please start Docker first."
    exit 1
fi

# Stop any existing container
echo "Stopping any existing container..."
docker stop instagram-service 2>/dev/null || true
docker rm instagram-service 2>/dev/null || true

# Build the Docker image
echo "Building Docker image..."
docker build -t instagram-service .

if [ $? -ne 0 ]; then
    echo "Failed to build Docker image"
    exit 1
fi

# Start LocalStack (if not already running)
echo "Starting LocalStack..."
docker run -d \
    --name localstack \
    -p 4566:4566 \
    -e SERVICES=s3,dynamodb,iam,lambda,apigateway \
    -e DEBUG=1 \
    -e DATA_DIR=/tmp/localstack/data \
    -v /var/run/docker.sock:/var/run/docker.sock \
    localstack/localstack:1.4

# Wait a moment for LocalStack to start
echo "Waiting for LocalStack to start..."
sleep 10

# Install required tools and configure AWS CLI
echo "Setting up AWS CLI and tools..."
if ! command -v aws &> /dev/null; then
    echo "Installing AWS CLI..."
    pip3 install awscli
fi

if ! command -v zip &> /dev/null; then
    echo "Installing zip..."
    apt update && apt install -y zip
fi

# Configure AWS CLI for LocalStack
echo "Configuring AWS CLI..."
aws configure set aws_access_key_id test
aws configure set aws_secret_access_key test
aws configure set default.region us-east-1
aws configure set default.output json

# Deploy AWS resources
echo "Deploying AWS resources..."
chmod +x deploy.sh
./deploy.sh

# Run the application container
echo "Starting application..."
docker run -d \
    --name instagram-service \
    --network host \
    -e AWS_DEFAULT_REGION=us-east-1 \
    -e AWS_ENDPOINT_URL=http://localhost:4566 \
    -e AWS_ACCESS_KEY_ID=test \
    -e AWS_SECRET_ACCESS_KEY=test \
    -e PORT=8080 \
    instagram-service

if [ $? -eq 0 ]; then
    echo "Application started successfully!"
    echo "API available at: http://localhost:8080"
    echo "Health check: http://localhost:8080/health"
    echo ""
    echo "To view logs: docker logs -f instagram-service"
    echo "To stop: ./stop.sh"
    echo ""
    echo "Test APIs with Postman:"
    echo "   Health: GET http://localhost:8080/health"
    echo "   Upload URL: POST http://localhost:8080/upload-url"
    echo "   List Images: GET http://localhost:8080/images?user_id=test_user"
else
    echo "Failed to start application"
    exit 1
fi
