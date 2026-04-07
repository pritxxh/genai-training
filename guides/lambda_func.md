# Lambda & API Gateway Guide

Concepts covered here are ones that've been properly understood and challenged.

---

## Lambda — Serverless Functions

Lambda runs your code only when triggered. No server to manage, no idle cost.

```
Traditional: [Server ON] ── always running ──> costs money 24/7
Lambda:      [nothing] ... [trigger] ... [runs 200ms] ... [gone]
```

Every Lambda function has:
1. a handler — the entry point AWS calls
2. a trigger — what invokes it (HTTP request, S3 event, schedule, etc.)
3. a role — what AWS services it's allowed to touch

### Handler structure

```python
def lambda_handler(event, context):
    # event = the input (HTTP request body, S3 event, etc.)
    # context = metadata (timeout remaining, function name, etc.)
    return {"statusCode": 200, "body": "..."}
```

### Deploy & update

```bash
# Package
cd smartdocs-ai/functions/generate-upload-url
zip function.zip handler.py

# Deploy (first time)
aws lambda create-function \
  --function-name smartdocs-generate-upload-url \
  --runtime python3.12 \
  --role arn:aws:iam::347152105990:role/smartdocs-lambda-role \
  --handler handler.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 10 \
  --region us-east-1

# Update code (after changes)
aws lambda update-function-code \
  --function-name smartdocs-generate-upload-url \
  --zip-file fileb://function.zip \
  --region us-east-1
```

### Test locally (simulates API Gateway event)

```python
import json
from handler import lambda_handler

event = {"body": json.dumps({"filename": "test.txt", "content_type": "text/plain"})}
result = lambda_handler(event, {})
print(json.loads(result["body"]))
```

### Debug with CloudWatch logs

Every `print()` in your handler goes to CloudWatch automatically.

```bash
aws logs tail /aws/lambda/smartdocs-generate-upload-url --follow --region us-east-1
```

Cold start = first invocation spins up a fresh container (slower).
Warm start = subsequent invocations reuse the container (faster).

---

## API Gateway — HTTP Endpoint

API Gateway sits in front of Lambda and exposes it over HTTPS.

```
Browser → POST /documents → API Gateway → Lambda → response → Browser
```

Three concepts:
- Route = method + path (e.g. POST /documents)
- Integration = how API Gateway connects to Lambda (AWS_PROXY passes the full request)
- Stage = deployment environment (dev, prod). Appears in the URL.

### Setup

```bash
# Create the HTTP API
aws apigatewayv2 create-api \
  --name smartdocs-api \
  --protocol-type HTTP \
  --region us-east-1

# Create Lambda integration
aws apigatewayv2 create-integration \
  --api-id $API_ID \
  --integration-type AWS_PROXY \
  --integration-uri $LAMBDA_ARN \
  --payload-format-version 2.0 \
  --region us-east-1

# Create route
aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "POST /documents" \
  --target integrations/<IntegrationId> \
  --region us-east-1

# Deploy stage
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

### Test the live endpoint

```bash
# Generate presigned upload URL
curl -X POST https://<ApiId>.execute-api.us-east-1.amazonaws.com/dev/documents \
  -H "Content-Type: application/json" \
  -d '{"filename": "test.txt", "content_type": "text/plain"}'

# Count characters in an S3 file
curl -X POST https://<ApiId>.execute-api.us-east-1.amazonaws.com/dev/documents \
  -H "Content-Type: application/json" \
  -d '{"s3_key": "documents/test.txt", "count_characters": true}'

# Count words in a S3 file 
curl -X POST https://<ApiID>.execute-api.us-east-1.amazonaws.com/dev/documents \
  -H "Content-Type: application/json" \
  -d '{"s3_key": "documents/test.txt", "count_words": true}'
```

The presigned URL flow (production pattern):
1. Client calls API → gets presigned URL + s3_key
2. Client PUTs file bytes directly to the presigned URL (no AWS credentials needed)
3. File lands in S3
4. Client calls API with s3_key to do further processing

The POST call only sends the filename as a string — no file bytes. The actual upload is a separate PUT to the presigned URL.
