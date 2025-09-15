# S3 client for presigned URL operations
import os
import boto3
from botocore.exceptions import ClientError

S3 = boto3.client('s3', endpoint_url=os.environ.get('AWS_ENDPOINT_URL'))

def generate_presigned_upload_url(bucket, key, content_type, expires_in=300):
    """Generate presigned URL for S3 upload"""
    return S3.generate_presigned_url(
        'put_object',
        Params={'Bucket': bucket, 'Key': key, 'ContentType': content_type},
        ExpiresIn=expires_in
    )

def generate_presigned_download_url(bucket, key, expires_in=3600):
    """Generate presigned URL for S3 download"""
    return S3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=expires_in)

def check_file_exists(bucket, key):
    """Check if file exists in S3"""
    try:
        S3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError:
        return False

def get_file_metadata(bucket, key):
    """Get file metadata from S3"""
    response = S3.head_object(Bucket=bucket, Key=key)
    return {
        'file_size': response['ContentLength'],
        'content_type': response['ContentType'],
        'last_modified': response['LastModified'].isoformat()
    }

def delete_s3_object(bucket, key):
    """Delete file from S3"""
    S3.delete_object(Bucket=bucket, Key=key)
