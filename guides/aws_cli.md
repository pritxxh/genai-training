# AWS CLI Guide

Concepts covered here are ones that've been properly understood and challenged.

---

## Setup & Identity

```bash
# Check AWS CLI version
aws --version

# Check current configuration
aws configure list

# Configure with IAM credentials
aws configure
# Prompts: Access Key ID, Secret Access Key, region (us-east-1), output format (json)

# Verify who you're logged in as — should NEVER show :root
aws sts get-caller-identity
```

Rule: never use root credentials for CLI. Always create an IAM user.

The ARN format tells you everything about a resource:
`arn:aws:service:region:account-id:resource`

---

## IAM — Identity & Access Management

Nothing in AWS trusts anything by default. Every action needs explicit permission.

```bash
# Create a non-root IAM user
aws iam create-user --user-name smartdocs-dev

# Attach a managed policy to the user
aws iam attach-user-policy \
  --user-name smartdocs-dev \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Create CLI access keys for the user
aws iam create-access-key --user-name smartdocs-dev

# Create a role (used by services like Lambda, not humans)
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

# Attach an inline policy to a role
aws iam put-role-policy \
  --role-name smartdocs-lambda-role \
  --policy-name smartdocs-lambda-policy \
  --policy-document file://smartdocs-ai/infra/lambda-role-policy.json

# Fix a role's trust policy (who can assume it)
aws iam update-assume-role-policy \
  --role-name smartdocs-lambda-role \
  --policy-document '{ ... }'
```

Key mental model:
- User = a human, has access keys
- Role = a badge for a service (Lambda, EC2), assumed at runtime
- Policy = the list of allowed actions attached to a user or role

---

## S3 — Object Storage

S3 stores files (objects) inside buckets. Bucket names are globally unique across all of AWS.

```bash
# Fetch all created API in past
aws apigatewayv2 get-apis --region us-east-1

# Create a bucket
aws s3api create-bucket \
  --bucket smartdocs-ai-347152105990 \
  --region us-east-1

# Block all public access
aws s3api put-public-access-block \
  --bucket smartdocs-ai-347152105990 \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket smartdocs-ai-347152105990 \
  --versioning-configuration Status=Enabled

# Upload a file
aws s3 cp test.txt s3://smartdocs-ai-347152105990/documents/test.txt

# List files
aws s3 ls s3://smartdocs-ai-347152105990/documents/
```

Key concepts:
- Bucket = container
- Object = any file
- Key = the file's full path inside the bucket (e.g. `documents/test.txt`)
- Presigned URL = a temporary, cryptographically signed URL that lets anyone upload/download without AWS credentials. Expires after N seconds.

`aws s3 cp` is for developers with credentials. Presigned URLs are for end users with no credentials.

---

## SNS — Simple Notification Service

SNS is AWS's pub/sub messaging service. An alarm, Lambda, or any AWS service can publish to an SNS topic, and all subscribers (email, SMS, Lambda, SQS) receive the message.

Think of it like a group chat — one message sent to the topic, everyone subscribed gets it.

```bash
# Create a topic — returns a TopicArn, save it
aws sns create-topic --name smartdocs-lambda-alerts --region us-east-1

# Subscribe an email address to the topic
# AWS sends a confirmation email — you MUST click it before notifications work
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:347152105990:smartdocs-lambda-alerts \
  --protocol email \
  --notification-endpoint your@email.com \
  --region us-east-1

# List all subscriptions for a topic
aws sns list-subscriptions-by-topic \
  --topic-arn arn:aws:sns:us-east-1:347152105990:smartdocs-lambda-alerts \
  --region us-east-1
```

Key concepts:
- Topic = the channel. Publishers send to it, subscribers receive from it.
- Subscription = a specific endpoint (email, Lambda, SQS) attached to a topic
- `pending confirmation` = subscription exists but email not confirmed yet — no messages delivered until confirmed
- A pending subscription can't be unsubscribed via CLI until confirmed — just re-subscribe with the correct email

---

## CloudWatch — Alarms

CloudWatch collects metrics from every AWS service automatically. An alarm watches one metric and changes state when a threshold is crossed.

Three states:
- `OK` — metric is within threshold
- `ALARM` — threshold breached, actions fire
- `INSUFFICIENT_DATA` — not enough data points yet (normal for new alarms)

```bash
# Create an alarm — fires when Lambda errors >= 3 in a 5-minute window
aws cloudwatch put-metric-alarm \
  --alarm-name "smartdocs-lambda-errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --dimensions Name=FunctionName,Value=smartdocs-generate-upload-url \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 3 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --statistic Sum \
  --alarm-actions arn:aws:sns:us-east-1:347152105990:smartdocs-lambda-alerts \
  --region us-east-1

# Verify the alarm was created
aws cloudwatch describe-alarms \
  --alarm-names "smartdocs-lambda-errors" \
  --region us-east-1
```

Key parameters explained:
- `--namespace AWS/Lambda` — Lambda metrics live here, not just "Lambda"
- `--period 300` — one data point = 5 minutes of aggregated errors
- `--evaluation-periods 1` — alarm after 1 consecutive breaching period
- `--statistic Sum` — add up all errors in the period (not average, not max)
- `--comparison-operator GreaterThanOrEqualToThreshold` — fire at exactly 3, not just above 3
- `--alarm-actions` — SNS topic ARN to notify when alarm fires

Why `Sum` not `Average`? If you had 10 invocations and 3 errors, average = 0.3 which would never breach a threshold of 3. Sum = 3 which triggers correctly.
