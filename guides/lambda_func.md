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

---

## S3 Event Triggers

Instead of manually calling an API to process a file, S3 can automatically invoke a Lambda the moment a file is uploaded. This is called an event-driven architecture.

```
Manual flow:    upload → call API with s3_key → Lambda processes → DynamoDB
Event-driven:   upload → S3 fires event → Lambda processes → DynamoDB (automatic)
```

The client never needs to make a second call. Processing happens in the background.

### How the event object changes

API Gateway sends an HTTP request — your Lambda reads `event["body"]`.
S3 sends a notification — your Lambda reads `event["Records"][0]["s3"]`.

```python
# S3 event structure
record = event["Records"][0]
bucket = record["s3"]["bucket"]["name"]
key    = record["s3"]["object"]["key"]
```

`Records` is always a list because S3 can batch multiple file events into one notification. In practice it's usually one item, but always index with `[0]`.

### Is it asynchronous?

Yes. The client uploads and gets a response immediately. Lambda fires in the background — the client doesn't wait for processing to finish. This is the right pattern for anything that takes time (counting, analysing, resizing images, etc.).

### Does Lambda run in the background waiting for events?

No — and this is the key insight about serverless. Lambda is not a running process. There's no idle container sitting there waiting. AWS's infrastructure listens for S3 events at the platform level and only spins up your Lambda when an event actually fires.

```
Traditional server:  [always ON] ──────────────────────> costs money 24/7
Lambda:              [nothing]...[event 50ms]...[nothing]...[event 30ms]
                                  ↑ pay here              ↑ pay here
```

S3 event triggers are actually cheaper than manual API calls for processing — not more expensive.

### Wiring it up via CLI

```bash
# 1. Deploy the trigger Lambda (separate function from the HTTP handler)
cd smartdocs-ai/functions/s3-trigger
zip function.zip handler.py

aws lambda create-function \
  --function-name smartdocs-s3-notification-event-trigger \
  --runtime python3.12 \
  --role arn:aws:iam::347152105990:role/smartdocs-lambda-role \
  --handler handler.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 10 \
  --region us-east-1

# 2. Grant S3 permission to invoke Lambda
# Principal is s3.amazonaws.com — S3 is the caller here, not a human or API Gateway
aws lambda add-permission \
  --function-name smartdocs-s3-notification-event-trigger \
  --statement-id s3-invoke \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::smartdocs-ai-347152105990 \
  --region us-east-1

# 3. Configure S3 to fire the notification on any object creation
aws s3api put-bucket-notification-configuration \
  --bucket smartdocs-ai-347152105990 \
  --notification-configuration '{
    "LambdaFunctionConfigurations": [{
      "LambdaFunctionArn": "arn:aws:lambda:us-east-1:347152105990:function:smartdocs-s3-notification-event-trigger",
      "Events": ["s3:ObjectCreated:*"]
    }]
  }'

# 4. Test — upload a file and watch it process automatically
aws s3 cp test.txt s3://smartdocs-ai-347152105990/documents/auto-test.txt

# 5. Verify in CloudWatch and DynamoDB
aws logs tail /aws/lambda/smartdocs-s3-notification-event-trigger --follow --region us-east-1
aws dynamodb scan --table-name smartdocs-documents --region us-east-1
```

### Why a separate Lambda function?

The HTTP handler (`generate-upload-url`) is triggered by API Gateway and returns HTTP responses. The S3 trigger handler has no HTTP client — it just processes and logs. Mixing them would mean checking `if "Records" in event` everywhere and returning different response formats. Separate functions = cleaner, easier to debug, easier to give different IAM permissions.

### The full production flow

```
1. Client calls POST /documents → gets presigned URL + s3_key
2. Client PUTs file directly to presigned URL (no AWS credentials needed)
3. File lands in S3
4. S3 fires event → Lambda trigger processes automatically
5. Results saved to DynamoDB
6. Client can query results via GET /documents/{doc_id}
```
