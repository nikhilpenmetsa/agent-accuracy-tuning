# Knowledge Base Stack

Bedrock Knowledge Base with HR documents for AI-powered Q&A. Provides semantic search over company policies and procedures.

## What It Does

Creates an AWS stack with:
- S3 bucket for HR documents
- OpenSearch Serverless collection for vector storage
- Bedrock Knowledge Base with Titan embeddings
- IAM roles and security policies

## Setup

1. Ensure `../config.env` exists with:
```bash
PROJECT_NAME=your-project-name
AWS_REGION=us-east-1
```

2. Copy environment template:
```bash
cp .env.example .env
```

3. Customize `.env` if needed (embedding model, paths, etc.)

## How to Run

```bash
# Deploy in sequence
bash 1-deploy-infrastructure.sh    # ~5-10 min
bash 2-setup-knowledge-base.sh     # ~1-2 min
bash 3-ingest-documents.sh         # ~2-5 min

# Test it works
bash 4-test-knowledge-base.sh

# Clean up
bash cleanup.sh
```

## Configuration

Stack name is automatically set to `${PROJECT_NAME}-kb-stack` using the PROJECT_NAME from `../config.env`.

Documents are loaded from `../hr-docs/` directory (9 markdown files covering benefits, PTO, compensation, etc.)

## What Gets Created

**Infrastructure (Step 1):**
- S3 bucket for document storage
- IAM role with Bedrock and OpenSearch permissions
- OpenSearch Serverless collection with security policies

**Knowledge Base (Step 2):**
- OpenSearch index with vector mappings (1024 dimensions)
- Bedrock Knowledge Base using Titan embeddings
- S3 data source connection

**Documents (Step 3):**
- HR documents uploaded to S3
- Ingestion job processes and vectorizes content
- Ready for semantic search queries

## Usage

After deployment, query the knowledge base:

**Via AWS CLI:**
```bash
aws bedrock-agent-runtime retrieve \
  --knowledge-base-id <KB_ID> \
  --retrieval-query text="What is the PTO policy?" \
  --region us-east-1
```

**Via AWS Console:**
Bedrock > Knowledge Bases > Select your KB > Test

**In Applications:**
Use the Knowledge Base ID from `kb_config.json` to integrate with Bedrock Agents or your own applications.

## Updating Documents

To update HR documents after initial deployment:

1. Modify files in `../hr-docs/`
2. Run: `bash 3-ingest-documents.sh`

The script will sync changes and re-ingest automatically.
