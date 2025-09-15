# Instagram Image Service

A simple image service for uploading and managing images using AWS services.

## How to Start

1. Run this command to start everything:
```bash
./start.sh
```

2. Wait for the message "Application started successfully!"

## How to Stop

Run this command to stop everything:
```bash
./stop.sh
```

## API Endpoints

All APIs are available at: `http://localhost:8080`

### 1. Check if service is running
```bash
curl http://localhost:8080/health
```
**Response:**
```json
{
  "service": "instagram-image-service",
  "status": "healthy"
}
```

### 2. Get upload URL
```bash
curl -X POST http://localhost:8080/upload-url \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "john",
    "filename": "photo.jpg",
    "content_type": "image/jpeg",
    "tags": ["vacation"]
  }'
```
**Response:**
```json
{
  "upload_url": "http://localhost:4566/instagram-images-local/john/photo.jpg?...",
  "image_id": "photo.jpg",
  "expires_in": 300
}
```

### 3. Upload your image
Copy the `upload_url` from step 2 and use it to upload your image:
```bash
curl -X PUT "PASTE_UPLOAD_URL_HERE" \
  -H "Content-Type: image/jpeg" \
  --data-binary @your_image.jpg
```

### 4. Confirm upload
```bash
curl -X POST http://localhost:8080/confirm-upload \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "john",
    "image_id": "photo.jpg"
  }'
```
**Response:**
```json
{
  "message": "Upload confirmed successfully",
  "image_id": "photo.jpg"
}
```

### 5. List all images
```bash
curl "http://localhost:8080/images?user_id=john"
```
**Response:**
```json
{
  "images": [
    {
      "user_id": "john",
      "image_id": "photo.jpg",
      "filename": "photo.jpg",
      "content_type": "image/jpeg",
      "file_size": 1024000,
      "tags": ["vacation"],
      "created_at": "2023-01-01T12:00:00Z",
      "status": "uploaded",
      "download_url": "http://localhost:4566/instagram-images-local/john/photo.jpg?..."
    }
  ]
}
```

### 6. Get one image
```bash
curl "http://localhost:8080/images/john/photo.jpg"
```
**Response:**
```json
{
  "user_id": "john",
  "image_id": "photo.jpg",
  "filename": "photo.jpg",
  "content_type": "image/jpeg",
  "file_size": 1024000,
  "tags": ["vacation"],
  "created_at": "2023-01-01T12:00:00Z",
  "status": "uploaded",
  "download_url": "http://localhost:4566/instagram-images-local/john/photo.jpg?..."
}
```

### 7. Delete image
```bash
curl -X DELETE "http://localhost:8080/images/john/photo.jpg"
```
**Response:**
```json
{
  "message": "Image deleted successfully",
  "image_id": "photo.jpg"
}
```

## Complete Example

Here's how to upload an image step by step:

1. **Start the service:**
```bash
./start.sh
```

2. **Get upload URL:**
```bash
curl -X POST http://localhost:8080/upload-url \
  -H "Content-Type: application/json" \
  -d '{"user_id": "john", "filename": "photo.jpg", "content_type": "image/jpeg", "tags": ["vacation"]}'
```

3. **Upload your image** (replace URL with the one from step 2):
```bash
curl -X PUT "http://localhost:4566/instagram-images-local/john/photo.jpg?..." \
  -H "Content-Type: image/jpeg" \
  --data-binary @your_image.jpg
```

4. **Confirm upload:**
```bash
curl -X POST http://localhost:8080/confirm-upload \
  -H "Content-Type: application/json" \
  -d '{"user_id": "john", "image_id": "photo.jpg"}'
```

5. **Check your images:**
```bash
curl "http://localhost:8080/images?user_id=john"
```

## Troubleshooting

- If you get "connection refused", make sure the service is running with `./start.sh`
- If upload fails, check that your image file exists and the path is correct
- If you get errors, check the logs with: `docker logs instagram-service`

## Stop the service

When you're done testing:
```bash
./stop.sh
```