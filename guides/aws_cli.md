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
