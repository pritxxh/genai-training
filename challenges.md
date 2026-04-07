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

---

## Current Challenge

### Challenge 8 — DynamoDB: Store Word Count Results
Create a DynamoDB table called `smartdocs-documents` with `doc_id` (String) as the partition key. Then extend the Lambda's word count action to write a new item to the table after every successful count. The item should store: `doc_id`, `s3_key`, `word_count`, `character_count`, and `uploaded_at` timestamp.

Things to figure out:
- How do you create a DynamoDB table via CLI?
- How do you give Lambda permission to write to DynamoDB?
- How do you use `boto3` to put an item into a DynamoDB table?
- What happens if you call word count on the same file twice — do you get duplicate items?

---

## Upcoming Challenges

### Challenge 9 — Read Back from DynamoDB
Write a new Lambda action that accepts a `doc_id` and returns the stored stats for that document from DynamoDB. What CLI command lets you fetch a single item by its partition key? What's the difference between `get-item` and `scan`?

### Challenge 10 — List All Documents
Add an action that returns all items stored in the DynamoDB table. Understand why `scan` is expensive and when you'd use a query instead. Add a limit so it never returns more than 20 items at once.

### Challenge 11 — S3 Event Trigger
Remove the manual word count call. Instead, configure S3 to automatically trigger the Lambda whenever a new `.txt` file is uploaded to the bucket. The Lambda should count words and store results in DynamoDB without any API call needed.

### Challenge 12 — Input Validation Layer
Right now the Lambda does basic validation inline. Refactor it: create a separate `validate(body)` function that checks all inputs before any action runs. It should return a list of errors, not just the first one it finds.

### Challenge 13 — CloudWatch Alarm
Set up a CloudWatch alarm that fires when your Lambda throws more than 3 errors in a 5-minute window. Where do Lambda errors show up? What metric do you watch? What can an alarm actually do when it triggers?

### Challenge 14 — Multi-file Batch Word Count
Add a new action that accepts a list of `s3_key` values and returns word counts for all of them in a single response. Think about error handling — if one file doesn't exist, should the whole request fail or should it return partial results?

### Challenge 15 — Docker: Containerise the Lambda
Package the Lambda as a Docker container image instead of a `.zip`. Push it to Amazon ECR (Elastic Container Registry). Deploy the Lambda using the container image. Understand why you'd choose a container over a zip (hint: think about dependencies and size limits).

### Challenge 16 — Linux: Shell Script for Deployment
Write a bash script `deploy.sh` that automates the full deploy process: zip the function, update Lambda, and print the live API URL. No manual steps. Understand file permissions (`chmod +x`), variables in bash, and exit codes.

### Challenge 17 — AWS Bedrock: Summarise a Document
Invoke an AWS Bedrock foundation model (e.g. Claude) from Lambda to generate a one-paragraph summary of a `.txt` file stored in S3. What IAM permissions does Lambda need? How do you structure the prompt? How do you parse the model's response?

### Challenge 18 — Gen-AI: RAG Pipeline (Retrieval Augmented Generation)
Build a basic RAG pipeline: upload a document → chunk it → generate embeddings → store in a vector database → query it with a natural language question → return a grounded answer. This is the foundation of most production Gen-AI apps.
