# Flask app for local testing
import os
import json
from flask import Flask, request, jsonify
from service.handler import (
    upload_url_handler,
    confirm_upload_handler,
    list_images_handler,
    get_image_handler,
    delete_image_handler
)

app = Flask(__name__)

def create_event(payload=None, query_params=None, path_params=None):
    """Create Lambda event from Flask request"""
    event = {}
    if payload:
        event['body'] = json.dumps(payload)
    if query_params:
        event['queryStringParameters'] = query_params
    if path_params:
        event['pathParameters'] = path_params
    return event

@app.route('/upload-url', methods=['POST'])
def upload_url():
    """Request presigned URL for image upload"""
    event = create_event(payload=request.get_json())
    res = upload_url_handler(event, None)
    return (res['body'], res['statusCode'], {'Content-Type': 'application/json'})

@app.route('/confirm-upload', methods=['POST'])
def confirm_upload():
    """Confirm image upload completion"""
    event = create_event(payload=request.get_json())
    res = confirm_upload_handler(event, None)
    return (res['body'], res['statusCode'], {'Content-Type': 'application/json'})

@app.route('/images', methods=['GET'])
def list_images():
    """List images with filters"""
    event = create_event(query_params=request.args.to_dict())
    res = list_images_handler(event, None)
    return (res['body'], res['statusCode'], {'Content-Type': 'application/json'})

@app.route('/images/<user_id>/<image_id>', methods=['GET'])
def get_image(user_id, image_id):
    """Get single image details"""
    event = create_event(path_params={'user_id': user_id, 'image_id': image_id})
    res = get_image_handler(event, None)
    return (res['body'], res['statusCode'], {'Content-Type': 'application/json'})

@app.route('/images/<user_id>/<image_id>', methods=['DELETE'])
def delete_image(user_id, image_id):
    """Delete image"""
    event = create_event(path_params={'user_id': user_id, 'image_id': image_id})
    res = delete_image_handler(event, None)
    return (res['body'], res['statusCode'], {'Content-Type': 'application/json'})

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'instagram-image-service'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=True)
