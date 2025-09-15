#!/usr/bin/env bash
# Deploy Lambda and API Gateway into LocalStack

AWS="aws --endpoint-url=http://localhost:4566"
BUCKET=instagram-images-local
TABLE=Images
LAMBDA_NAME=instagram-image-service-lambda
ROLE_NAME=lambda-basic-execution

echo "Deploying Instagram Image Service to LocalStack..."

# 1) Ensure resources exist
echo "Creating S3 bucket..."
$AWS s3api create-bucket --bucket $BUCKET || true

echo "Creating DynamoDB table..."
$AWS dynamodb create-table --table-name $TABLE \
  --attribute-definitions AttributeName=user_id,AttributeType=S AttributeName=image_id,AttributeType=S \
  --key-schema AttributeName=user_id,KeyType=HASH AttributeName=image_id,KeyType=RANGE \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 || true

# 2) Package lambda
echo "Packaging Lambda function..."
rm -f /tmp/handler.zip
zip -r /tmp/handler.zip service -x "*/__pycache__/*"

# 3) Create IAM role
echo "Creating IAM role..."
$AWS iam create-role --role-name $ROLE_NAME --assume-role-policy-document '{"Version": "2012-10-17","Statement": [{"Action": "sts:AssumeRole","Principal": {"Service": "lambda.amazonaws.com"},"Effect": "Allow","Sid": ""}]}' || true

# 4) Create or update lambda
echo "Creating/updating Lambda function..."
if $AWS lambda list-functions | grep -q $LAMBDA_NAME; then
  $AWS lambda update-function-code --function-name $LAMBDA_NAME --zip-file fileb:///tmp/handler.zip
else
  $AWS lambda create-function --function-name $LAMBDA_NAME --runtime python3.8 --handler service.handler.upload_url_handler --zip-file fileb:///tmp/handler.zip --role arn:aws:iam::000000000000:role/$ROLE_NAME
fi

# 5) Create API Gateway REST API
echo "Creating API Gateway..."
API_ID=$($AWS apigateway create-rest-api --name "instagram-api" --query 'id' --output text)
ROOT_ID=$($AWS apigateway get-resources --rest-api-id $API_ID --query 'items[0].id' --output text)

# Create resources and methods
echo "Setting up API routes..."

# /upload-url -> POST -> Lambda
UPLOAD_RES=$($AWS apigateway create-resource --rest-api-id $API_ID --parent-id $ROOT_ID --path-part upload-url --query 'id' --output text)
$AWS apigateway put-method --rest-api-id $API_ID --resource-id $UPLOAD_RES --http-method POST --authorization-type NONE
$AWS apigateway put-integration --rest-api-id $API_ID --resource-id $UPLOAD_RES --http-method POST --type AWS_PROXY --integration-http-method POST --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:000000000000:function:$LAMBDA_NAME/invocations"

# /confirm-upload -> POST -> Lambda
CONFIRM_RES=$($AWS apigateway create-resource --rest-api-id $API_ID --parent-id $ROOT_ID --path-part confirm-upload --query 'id' --output text)
$AWS apigateway put-method --rest-api-id $API_ID --resource-id $CONFIRM_RES --http-method POST --authorization-type NONE
$AWS apigateway put-integration --rest-api-id $API_ID --resource-id $CONFIRM_RES --http-method POST --type AWS_PROXY --integration-http-method POST --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:000000000000:function:$LAMBDA_NAME/invocations"

# /images -> GET -> Lambda
IMAGES_RES=$($AWS apigateway create-resource --rest-api-id $API_ID --parent-id $ROOT_ID --path-part images --query 'id' --output text)
$AWS apigateway put-method --rest-api-id $API_ID --resource-id $IMAGES_RES --http-method GET --authorization-type NONE
$AWS apigateway put-integration --rest-api-id $API_ID --resource-id $IMAGES_RES --http-method GET --type AWS_PROXY --integration-http-method POST --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:000000000000:function:$LAMBDA_NAME/invocations"

# Give permission to API Gateway to invoke Lambda
echo "Setting up Lambda permissions..."
$AWS lambda add-permission --function-name $LAMBDA_NAME --statement-id apigw-$LAMBDA_NAME --action lambda:InvokeFunction --principal apigateway.amazonaws.com || true

# Deploy API
echo "Deploying API..."
$AWS apigateway create-deployment --rest-api-id $API_ID --stage-name dev

echo "Deployment complete!"
echo "API Gateway URL: http://localhost:4566/restapis/$API_ID/dev/_user_request_"
echo "Available endpoints:"
echo "   POST /upload-url"
echo "   POST /confirm-upload"
echo "   GET /images"
echo "   GET /images/{user_id}/{image_id}"
echo "   DELETE /images/{user_id}/{image_id}"
