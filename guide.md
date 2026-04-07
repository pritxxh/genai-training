# SmartDocs AI — AWS Training Command Reference

---

## Module 1: First Time Setup

```bash
# Check AWS CLI version (install if nothing returns)
aws --version

# Check current AWS configuration
aws configure list

# Configure CLI with IAM user credentials
aws configure
# Prompts: Access Key ID, Secret Access Key, region (us-east-1), output format (json)

# Verify identity — should show user/smartdocs-dev, NOT root
aws sts get-caller-identity
```

Create or sign in to AWS console: https://console.aws.amazon.com

---

## Module 2: IAM User Setup

```bash
# Create a non-root IAM user for day-to-day work
aws iam create-user --user-name smartdocs-dev

# Attach admin policy (tighten later in production)
aws iam attach-user-policy \
  --user-name smartdocs-dev \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Generate CLI access keys for the new user
aws iam create-access-key --user-name smartdocs-dev
```

---

## Module 3: S3 — Document Storage

```bash
# Create the S3 bucket (name must be globally unique)
aws s3api create-bucket \
  --bucket smartdocs-ai-347152105990 \
  --region us-east-1

# Block all public access (documents are private)
aws s3api put-public-access-block \
  --bucket smartdocs-ai-347152105990 \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Enable versioning so files are never permanently lost
aws s3api put-bucket-versioning \
  --bucket smartdocs-ai-347152105990 \
  --versioning-configuration Status=Enabled

# Upload a file to S3
aws s3 cp test-doc.txt s3://smartdocs-ai-347152105990/documents/test-doc.txt

# List files in the bucket
aws s3 ls s3://smartdocs-ai-347152105990/documents/

# Upload test.txt for Lambda testing
aws s3 cp test.txt s3://smartdocs-ai-347152105990/documents/test.txt
```

---

## Module 4: Lambda — Serverless Functions

```bash
# Create the IAM role that Lambda will assume at runtime
aws iam create-role \
  --role-name smartdocs-lambda-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach S3 + CloudWatch Logs permissions to the role
aws iam put-role-policy \
  --role-name smartdocs-lambda-role \
  --policy-name smartdocs-lambda-policy \
  --policy-document file://smartdocs-ai/infra/lambda-role-policy.json

# Package the Lambda function
cd smartdocs-ai/functions/generate-upload-url
zip function.zip handler.py

# Deploy Lambda function
aws lambda create-function \
  --function-name smartdocs-generate-upload-url \
  --runtime python3.12 \
  --role arn:aws:iam::347152105990:role/smartdocs-lambda-role \
  --handler handler.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 10 \
  --region us-east-1

# Update function code after changes (use instead of create-function)
aws lambda update-function-code \
  --function-name smartdocs-generate-upload-url \
  --zip-file fileb://function.zip \
  --region us-east-1
```

### Testing Lambda Locally (no deployment needed)

```bash
cd smartdocs-ai/functions/generate-upload-url

python3 -c "
import json
from handler import lambda_handler

event = {
    'body': json.dumps({
        'filename': 'test.txt',
        'content_type': 'text/plain',
        'count_characters': True
    })
}

result = lambda_handler(event, {})
print(json.dumps(json.loads(result['body']), indent=2))
"
```

### Invoking Lambda via AWS CLI

```bash
# Invoke the deployed Lambda and write response to output.json
aws lambda invoke \
  --function-name smartdocs-generate-upload-url \
  --payload '{"body": "{\"filename\": \"test.txt\", \"content_type\": \"text/plain\", \"count_characters\": true}"}' \
  --cli-binary-format raw-in-base64-out \
  output.json \
  --region us-east-1

# Read the Lambda response
cat output.json

# Update Lambda code after changes
cd smartdocs-ai/functions/generate-upload-url
zip function.zip handler.py
aws lambda update-function-code \
  --function-name smartdocs-generate-upload-url \
  --zip-file fileb://function.zip \
  --region us-east-1

# Stream live Lambda logs (CloudWatch)
aws logs tail /aws/lambda/smartdocs-generate-upload-url --follow --region us-east-1
```

---

## Module 5: API Gateway — HTTP Endpoint

```bash
# Set shell variables (run in terminal, not a file)
API_ID=<your ApiId>
LAMBDA_ARN=arn:aws:lambda:us-east-1:347152105990:function:smartdocs-generate-upload-url

# Create the HTTP API
aws apigatewayv2 create-api \
  --name smartdocs-api \
  --protocol-type HTTP \
  --region us-east-1

# Create Lambda integration (AWS_PROXY passes full HTTP request into Lambda event)
aws apigatewayv2 create-integration \
  --api-id $API_ID \
  --integration-type AWS_PROXY \
  --integration-uri $LAMBDA_ARN \
  --payload-format-version 2.0 \
  --region us-east-1

# Create route — maps POST /documents to the integration
aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "POST /documents" \
  --target integrations/<IntegrationId> \
  --region us-east-1

# Deploy a stage (dev) — makes the API publicly accessible
aws apigatewayv2 create-stage \
  --api-id $API_ID \
  --stage-name dev \
  --auto-deploy \
  --region us-east-1

# Grant API Gateway permission to invoke Lambda
aws lambda add-permission \
  --function-name smartdocs-generate-upload-url \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:347152105990:$API_ID/*/*/documents" \
  --region us-east-1
```

### Testing the live API

```bash
# Generate a presigned upload URL
curl -X POST https://<ApiId>.execute-api.us-east-1.amazonaws.com/dev/documents \
  -H "Content-Type: application/json" \
  -d '{"filename": "test.txt", "content_type": "text/plain"}'

# Count characters in an existing S3 file
curl -X POST https://<ApiId>.execute-api.us-east-1.amazonaws.com/dev/documents \
  -H "Content-Type: application/json" \
  -d '{"s3_key": "documents/test.txt", "count_characters": true}'

# Fix IAM if you get AccessDenied on GetObject
aws iam put-role-policy \
  --role-name smartdocs-lambda-role \
  --policy-name smartdocs-lambda-policy \
  --policy-document file://smartdocs-ai/infra/lambda-role-policy.json
```

