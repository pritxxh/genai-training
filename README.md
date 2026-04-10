# AWS & Gen-AI Training Ground

A hands-on, self-paced learning repo for mastering AWS, serverless architecture, Linux, Docker, and Gen-AI — one real project at a time.

The approach here is simple: no concept gets added to a guide until it's been genuinely understood and challenged. Every project is built from scratch using the CLI, not the console.

---

## How This Repo Works

Each major concept gets its own project folder. As complexity grows, so does the project count. Guides live separately and are shared across projects — they document the *concepts*, not just the commands.

```
/
├── guides/                  # Concept guides (written after understanding, not before)
│   ├── guide_aws_cli.md     # AWS CLI, IAM, S3
│   ├── guide_lambda_func.md # Lambda, API Gateway
│   └── dynamoDB.md          # DynamoDB (in progress)
├── smartdocs-ai/            # Project 1 — document processing backend
├── <next-project>/          # Project 2 — coming as new concepts are introduced
├── challenges.md            # All challenges, past and upcoming
├── .env                     # Shared AWS identity (access keys, region, account ID)
└── .env.example             # Template — copy this, never commit the real one
```

Each project has its own `.env` for project-specific values (bucket names, Lambda ARNs, API IDs, table names). The root `.env` holds only the shared AWS identity that applies everywhere.

---

## Projects

### Project 1 — SmartDocs AI
> Status: In progress

A serverless document processing backend. Users upload `.txt` files via presigned S3 URLs and the system analyses them — word count, character count, and (soon) AI-powered summaries.

```
Client → API Gateway → Lambda → S3 / DynamoDB / Bedrock
```

Location: `smartdocs-ai/`

What's built so far:
- Presigned URL generation for direct S3 uploads
- Character count on uploaded `.txt` files
- Word count on uploaded `.txt` files
- Single `POST /documents` endpoint via API Gateway

What's next:
- Store results in DynamoDB
- S3 event trigger (auto-process on upload)
- AI summarisation via AWS Bedrock

---

## Learning Roadmap

This is the full arc — from CLI basics to production Gen-AI pipelines.

### AWS Foundations
- [x] AWS CLI setup & IAM (users, roles, policies)
- [x] S3 — buckets, objects, presigned URLs
- [x] Lambda — serverless functions, packaging, deploying
- [x] API Gateway — HTTP APIs, routes, integrations, stages
- [x] DynamoDB — tables, items, partition keys, put/get/scan, TypeDeserializer
- [x] S3 event triggers — auto-invoke Lambda on upload
- [x] Input validation layer — shared modules, action routing, handle_* pattern
- [x] Deploy scripts — deploy.sh, set -e, zip structure
- [ ] CloudWatch — structured logging, metrics, alarms
- [ ] DynamoDB advanced — queries, GSI, scan vs query

### Gen-AI on AWS
- [ ] AWS Bedrock — invoking foundation models (Claude, Titan, etc.)
- [ ] Bedrock + Lambda — summarise documents with an LLM
- [ ] Embeddings — turning text into vectors
- [ ] Vector search — Amazon OpenSearch or pgvector
- [ ] RAG pipeline — upload → chunk → embed → search → answer

### Infrastructure & DevOps
- [ ] Linux fundamentals — file system, permissions, shell scripting
- [ ] Docker — containers, images, Dockerfile, local dev
- [ ] Docker + Lambda — containerised Lambda functions
- [ ] Infrastructure as Code — AWS CDK or Terraform
- [ ] CI/CD — automated deployments with GitHub Actions

---

## Guides

Guides are written *after* a concept is understood — not as a reference copied from docs, but as a personal record of what was learned, what tripped us up, and how it actually works.

| Guide | Covers |
|---|---|
| `guides/guide_aws_cli.md` | AWS CLI setup, IAM users/roles/policies, S3 |
| `guides/guide_lambda_func.md` | Lambda handler, deploy/update, API Gateway wiring |
| `guides/dynamoDB.md` | DynamoDB concepts, table design, CLI (in progress) |

---

## Challenges

All challenges are in `challenges.md`. No solutions — the point is to figure it out. Guides are there if you get truly stuck, but try the challenge first.

---

## Getting Started

### Prerequisites
- AWS account (free tier is fine)
- AWS CLI installed
- Python 3.12+
- Basic terminal comfort

### Setup

```bash
# Clone the repo
git clone <repo-url>

# Set up shared AWS credentials
cp .env.example .env
# Fill in your AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_ACCOUNT_ID, AWS_REGION

# For a specific project, set up its own .env
cp smartdocs-ai/.env.example smartdocs-ai/.env
# Fill in project-specific values
```

Configure the AWS CLI:
```bash
aws configure
aws sts get-caller-identity  # should show your IAM user, never root
```

---

## Ground Rules

- Never commit real credentials — `.env` files are in `.gitignore`
- Never use root credentials for CLI work — always an IAM user
- No concept goes into a guide until it's been challenged and understood
- Each project gets its own `.env` — don't mix project-specific values in the root one
