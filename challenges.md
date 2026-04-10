# SmartDocs AI — Challenges

These are real challenges worked through during this training. No solutions here — the point is to struggle with them first. Check the guides only after you've given it a genuine shot.

---

## Completed Challenges

### Challenge 1 — AWS Identity & First Setup
Set up the AWS CLI from scratch. Configure it with a non-root IAM user. Verify you're not accidentally using root credentials. Understand what the ARN format tells you about a resource.

### Challenge 2 — IAM Role for Lambda
Create an IAM role that Lambda can assume at runtime. Understand the difference between a user (human) and a role (service badge). Attach a policy that gives Lambda permission to read from S3 and write logs to CloudWatch.

### Challenge 3 — S3 Bucket Setup
Create a private S3 bucket. Block all public access. Enable versioning. Upload a test `.txt` file using the CLI. Understand the difference between `aws s3 cp` (for developers) and a presigned URL (for end users).

### Challenge 4 — First Lambda Function
Write a Lambda handler in Python that generates a presigned S3 upload URL. Package it into a `.zip`, deploy it via CLI, and invoke it. Understand cold starts vs warm starts and where `print()` logs go.

### Challenge 5 — API Gateway Wiring
Create an HTTP API in API Gateway. Wire it to your Lambda using `AWS_PROXY` integration. Create a `POST /documents` route. Deploy a `dev` stage. Grant API Gateway permission to invoke Lambda. Test the full flow with `curl`.

### Challenge 6 — Count Characters in a .txt File
Extend the existing Lambda to support a second action: reading a `.txt` file from S3 by its `s3_key` and returning the character count. Reject non-`.txt` files with a proper error. Handle the case where the file doesn't exist in S3.

### Challenge 7 — Count Words in a .txt File
Add a third action to the same Lambda: word count. The function must fetch the file from S3, decode it, split it into words, and return the count. Only `.txt` files allowed. Reuse the same API endpoint — no new routes needed. Package, deploy, and test via `curl`.

### Challenge 8 — DynamoDB: Store Word Count Results
Create a DynamoDB table called `smartdocs-documents` with `doc_id` (String) as the partition key. Extend the Lambda to write a new item to the table after every successful count. Store: `doc_id`, `s3_key`, `word_count`, `char_count`, and `timestamp`. Understand IAM permissions for DynamoDB and the boto3 type descriptor format.

### Challenge 9 — Read Back from DynamoDB
Add a `get` action that accepts a `doc_id` and returns the stored stats from DynamoDB. Use `get_item` not `scan`. Deserialise the response with `TypeDeserializer` and handle the `Decimal` serialisation issue in `json.dumps`.

### Challenge 10 — List All Documents
Add a `list` action that returns all items from DynamoDB with a `Limit`. Understand why `scan` is expensive at scale and add `dynamodb:Scan` to the IAM role policy.

### Challenge 11 — S3 Event Trigger
Deploy a separate Lambda function that fires automatically when a `.txt` file is uploaded to S3. Configure S3 bucket notifications via CLI. Grant S3 permission to invoke Lambda using `s3.amazonaws.com` as the principal. Understand async processing and why Lambda doesn't cost money while idle.

### Challenge 12 — Input Validation Layer
Refactor the HTTP handler: extract `validate(body, action)` into `shared/validate.py`, split each action into its own `handle_*` function, replace flag-based routing with an action routing dict. Understand `boto3.client` vs `boto3.resource`, shared module paths in Lambda, and correct zip structure.

### Challenge 16 — Deploy Scripts (done early)
Write `deploy.sh` for both Lambda functions. Use `set -e` to stop on failure. Fix zip structure to correctly include `shared/` folder. Add alias in `.zshrc` for one-command deploys. Understand `chmod +x` and why aliases don't scale across projects.

---

## Current Challenge

### Challenge 13 — CloudWatch Alarm
Set up a CloudWatch alarm that fires when your Lambda throws more than 3 errors in a 5-minute window. Where do Lambda errors show up? What metric do you watch? What can an alarm actually do when it triggers? What's the difference between a metric, an alarm, and an action?

---

## Upcoming Challenges

### Challenge 14 — Multi-file Batch Word Count
Add a new action that accepts a list of `s3_key` values and returns word counts for all of them in a single response. Think about error handling — if one file doesn't exist, should the whole request fail or should it return partial results?

### Challenge 15 — Docker: Containerise the Lambda
Package the Lambda as a Docker container image instead of a `.zip`. Push it to Amazon ECR (Elastic Container Registry). Deploy the Lambda using the container image. Understand why you'd choose a container over a zip (hint: think about dependencies and size limits).

### Challenge 17 — AWS Bedrock: Summarise a Document
Invoke an AWS Bedrock foundation model (e.g. Claude) from Lambda to generate a one-paragraph summary of a `.txt` file stored in S3. What IAM permissions does Lambda need? How do you structure the prompt? How do you parse the model's response?

### Challenge 18 — Gen-AI: RAG Pipeline (Retrieval Augmented Generation)
Build a basic RAG pipeline: upload a document → chunk it → generate embeddings → store in a vector database → query it with a natural language question → return a grounded answer. This is the foundation of most production Gen-AI apps.
