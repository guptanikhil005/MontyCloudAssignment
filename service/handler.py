# Lambda handlers for Instagram Image Service
import os
import json
from datetime import datetime
from decimal import Decimal

from .s3_client import (
    generate_presigned_upload_url, 
    generate_presigned_download_url,
    check_file_exists,
    get_file_metadata,
    delete_s3_object
)
from .dynamo_client import (
    put_image_metadata,
    get_images,
    get_image_metadata,
    update_image_status,
    delete_image_metadata
)

S3_BUCKET = os.environ.get('S3_BUCKET', 'instagram-images-local')
DDB_TABLE = os.environ.get('DDB_TABLE', 'Images')

def convert_decimals(obj):
    """Convert Decimal objects to regular numbers for JSON serialization"""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    else:
        return obj

def response(status_code, body):
    """Create Lambda response"""
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body)
    }

def upload_url_handler(event, context):
    """Generate presigned URL for image upload"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        required_fields = ['user_id', 'filename', 'content_type']
        for field in required_fields:
            if field not in body:
                return response(400, {'error': f'Missing required field: {field}'})
        
        user_id = body['user_id']
        filename = body['filename']
        content_type = body['content_type']
        
        # Generate unique image ID
        image_id = str(uuid.uuid4())
        
        # Create S3 key
        file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
        s3_key = f"{user_id}/{image_id}.{file_extension}"
        
        # Generate presigned URL
        upload_url = generate_presigned_upload_url(
            bucket=S3_BUCKET,
            key=s3_key,
            content_type=content_type,
            expires_in=300
        )
        
        # Store pending metadata in DynamoDB
        item = {
            'user_id': user_id,
            'image_id': image_id,
            'filename': filename,
            'content_type': content_type,
            's3_key': s3_key,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'caption': body.get('caption', ''),
            'tags': body.get('tags', [])
        }
        put_image_metadata(DDB_TABLE, item)
        
        return response(200, {
            'image_id': image_id,
            'upload_url': upload_url,
            'expires_in': 300
        })
        
    except Exception as e:
        return response(500, {'error': f'Upload URL generation failed: {str(e)}'})

def confirm_upload_handler(event, context):
    """Confirm image upload completion"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        if 'image_id' not in body:
            return response(400, {'error': 'Missing required field: image_id'})
        
        image_id = body['image_id']
        user_id = body.get('user_id')  # Optional, can be extracted from metadata
        
        # Get image metadata
        if user_id:
            image_metadata = get_image_metadata(DDB_TABLE, user_id, image_id)
        else:
            # If user_id not provided, we need to find it
            # This is a limitation of the current design - we'll require user_id
            return response(400, {'error': 'user_id is required'})
        
        if not image_metadata:
            return response(404, {'error': 'Image not found'})
        
        # Check if file exists in S3
        if not check_file_exists(S3_BUCKET, image_metadata['s3_key']):
            return response(400, {'error': 'File not found in S3'})
        
        # Get file metadata from S3
        file_metadata = get_file_metadata(S3_BUCKET, image_metadata['s3_key'])
        
        # Update DynamoDB with uploaded status and file size
        update_image_status(
            table_name=DDB_TABLE,
            user_id=user_id,
            image_id=image_id,
            status='uploaded',
            file_size=file_metadata['file_size']
        )
        
        return response(200, {
            'status': 'success',
            'image_id': image_id,
            'file_size': file_metadata['file_size']
        })
        
    except Exception as e:
        return response(500, {'error': f'Upload confirmation failed: {str(e)}'})

def list_images_handler(event, context):
    """List images with filters"""
    try:
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('user_id')
        tag = query_params.get('tag')
        start_date = query_params.get('start_date')
        end_date = query_params.get('end_date')
        
        if not user_id:
            return response(400, {'error': 'user_id is required'})
        
        # Get images from DynamoDB
        items = get_images(DDB_TABLE, user_id)
        
        # Filter by tag
        if tag:
            items = [i for i in items if tag in (i.get('tags') or [])]
        
        # Filter by date range
        if start_date or end_date:
            sd = start_date or '0000-01-01T00:00:00Z'
            ed = end_date or '9999-12-31T23:59:59Z'
            items = [i for i in items if sd <= i.get('created_at', '') <= ed]
        
        # Generate download URLs for uploaded images
        for item in items:
            if item.get('status') == 'uploaded':
                try:
                    item['download_url'] = generate_presigned_download_url(
                        bucket=S3_BUCKET,
                        key=item['s3_key'],
                        expires_in=3600
                    )
                except:
                    item['download_url'] = None
            else:
                item['download_url'] = None
        
        return response(200, {
            'count': len(items),
            'images': convert_decimals(items)
        })
        
    except Exception as e:
        return response(500, {'error': f'List images failed: {str(e)}'})

def get_image_handler(event, context):
    """Get single image details and download URL"""
    try:
        path_params = event.get('pathParameters') or {}
        user_id = path_params.get('user_id')
        image_id = path_params.get('image_id')
        
        if not user_id or not image_id:
            return response(400, {'error': 'user_id and image_id are required'})
        
        # Get image metadata
        item = get_image_metadata(DDB_TABLE, user_id, image_id)
        if not item:
            return response(404, {'error': 'Image not found'})
        
        # Generate download URL if image is uploaded
        if item.get('status') == 'uploaded':
            try:
                download_url = generate_presigned_download_url(
                    bucket=S3_BUCKET,
                    key=item['s3_key'],
                    expires_in=3600
                )
                item['download_url'] = download_url
            except:
                item['download_url'] = None
        else:
            item['download_url'] = None
        
        return response(200, convert_decimals(item))
        
    except Exception as e:
        return response(500, {'error': f'Get image failed: {str(e)}'})

def delete_image_handler(event, context):
    """Delete image from S3 and DynamoDB"""
    try:
        path_params = event.get('pathParameters') or {}
        user_id = path_params.get('user_id')
        image_id = path_params.get('image_id')
        
        if not user_id or not image_id:
            return response(400, {'error': 'user_id and image_id are required'})
        
        # Get image metadata
        item = get_image_metadata(DDB_TABLE, user_id, image_id)
        if not item:
            return response(404, {'error': 'Image not found'})
        
        # Delete from S3 if file exists
        if item.get('status') == 'uploaded' and item.get('s3_key'):
            try:
                delete_s3_object(S3_BUCKET, item['s3_key'])
            except Exception as e:
                # Log error but continue with DynamoDB deletion
                print(f"Failed to delete S3 file: {str(e)}")
        
        # Delete from DynamoDB
        delete_image_metadata(DDB_TABLE, user_id, image_id)
        
        return response(200, {
            'deleted': True,
            'image_id': image_id
        })
        
    except Exception as e:
        return response(500, {'error': f'Delete image failed: {str(e)}'})
