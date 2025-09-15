# DynamoDB client for metadata operations
import os
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

DDB = boto3.resource('dynamodb', endpoint_url=os.environ.get('AWS_ENDPOINT_URL'))

def put_image_metadata(table_name, item):
    """Store image metadata in DynamoDB"""
    table = DDB.Table(table_name)
    table.put_item(Item=item)

def get_images(table_name, user_id):
    """Get all images for a user"""
    table = DDB.Table(table_name)
    resp = table.query(KeyConditionExpression=Key('user_id').eq(user_id))
    return resp.get('Items', [])

def get_image_metadata(table_name, user_id, image_id):
    """Get specific image metadata"""
    table = DDB.Table(table_name)
    resp = table.get_item(Key={'user_id': user_id, 'image_id': image_id})
    return resp.get('Item')

def update_image_status(table_name, user_id, image_id, status, file_size=None):
    """Update image status and file size"""
    table = DDB.Table(table_name)
    update_expression = "SET #status = :status"
    expression_values = {':status': status}
    expression_names = {'#status': 'status'}
    
    if file_size:
        update_expression += ", file_size = :file_size"
        expression_values[':file_size'] = file_size
    
    table.update_item(
        Key={'user_id': user_id, 'image_id': image_id},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_values,
        ExpressionAttributeNames=expression_names
    )

def delete_image_metadata(table_name, user_id, image_id):
    """Delete image metadata from DynamoDB"""
    table = DDB.Table(table_name)
    table.delete_item(Key={'user_id': user_id, 'image_id': image_id})
