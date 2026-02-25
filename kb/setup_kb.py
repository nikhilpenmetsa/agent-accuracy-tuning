#!/usr/bin/env python3
"""
Setup script for Bedrock Knowledge Base
Creates OpenSearch index and Bedrock Knowledge Base resources
"""

import boto3
import json
import time
import sys
import os
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

def get_stack_outputs(stack_name, region):
    """Get CloudFormation stack outputs"""
    cfn = boto3.client('cloudformation', region_name=region)
    
    try:
        response = cfn.describe_stacks(StackName=stack_name)
        outputs = {}
        for output in response['Stacks'][0]['Outputs']:
            outputs[output['OutputKey']] = output['OutputValue']
        return outputs
    except Exception as e:
        print(f"Error getting stack outputs: {e}")
        sys.exit(1)

def create_opensearch_index(collection_endpoint, region):
    """Create OpenSearch Serverless index with vector mappings"""
    print("Creating OpenSearch Serverless index...")
    
    # Extract host from endpoint
    host = collection_endpoint.replace('https://', '')
    
    # Get credentials
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, region, 'aoss')
    
    # Create OpenSearch client
    client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=30
    )
    
    index_name = 'hr-docs-index'
    
    # Check if index already exists
    if client.indices.exists(index=index_name):
        print(f"  Index '{index_name}' already exists")
        return index_name
    
    # Create index with vector mappings
    index_body = {
        'settings': {
            'index': {
                'knn': True,
                'number_of_shards': 2,
                'number_of_replicas': 0
            }
        },
        'mappings': {
            'properties': {
                'vector': {
                    'type': 'knn_vector',
                    'dimension': 1024,
                    'method': {
                        'name': 'hnsw',
                        'engine': 'faiss',
                        'parameters': {
                            'ef_construction': 512,
                            'm': 16
                        }
                    }
                },
                'text': {
                    'type': 'text'
                },
                'metadata': {
                    'type': 'text',
                    'index': False
                },
                'AMAZON_BEDROCK_TEXT_CHUNK': {
                    'type': 'text'
                },
                'AMAZON_BEDROCK_METADATA': {
                    'type': 'text',
                    'index': False
                }
            }
        }
    }
    
    try:
        response = client.indices.create(index=index_name, body=index_body)
        print(f"  ✓ Index '{index_name}' created successfully")
        return index_name
    except Exception as e:
        print(f"  Error creating index: {e}")
        sys.exit(1)

def create_knowledge_base(outputs, region):
    """Create Bedrock Knowledge Base"""
    print("\nCreating Bedrock Knowledge Base...")
    
    # Wait a bit more for permissions to propagate
    print("  Waiting for IAM permissions to propagate...")
    time.sleep(30)
    
    bedrock = boto3.client('bedrock-agent', region_name=region)
    
    kb_name = 'hr-knowledge-base'
    
    try:
        response = bedrock.create_knowledge_base(
            name=kb_name,
            description='Knowledge Base for HR documents',
            roleArn=outputs['KnowledgeBaseRoleArn'],
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': outputs['EmbeddingModelArn']
                }
            },
            storageConfiguration={
                'type': 'OPENSEARCH_SERVERLESS',
                'opensearchServerlessConfiguration': {
                    'collectionArn': outputs['OpenSearchCollectionArn'],
                    'vectorIndexName': 'hr-docs-index',
                    'fieldMapping': {
                        'vectorField': 'vector',
                        'textField': 'AMAZON_BEDROCK_TEXT_CHUNK',
                        'metadataField': 'AMAZON_BEDROCK_METADATA'
                    }
                }
            }
        )
        
        kb_id = response['knowledgeBase']['knowledgeBaseId']
        print(f"  ✓ Knowledge Base created: {kb_id}")
        return kb_id
        
    except Exception as e:
        print(f"  Error creating knowledge base: {e}")
        sys.exit(1)

def create_data_source(kb_id, bucket_name, region):
    """Create S3 data source for Knowledge Base"""
    print("\nCreating S3 data source...")
    
    bedrock = boto3.client('bedrock-agent', region_name=region)
    
    try:
        response = bedrock.create_data_source(
            knowledgeBaseId=kb_id,
            name='hr-docs-s3-source',
            description='S3 data source for HR documents',
            dataSourceConfiguration={
                'type': 'S3',
                's3Configuration': {
                    'bucketArn': f'arn:aws:s3:::{bucket_name}'
                }
            }
        )
        
        ds_id = response['dataSource']['dataSourceId']
        print(f"  ✓ Data source created: {ds_id}")
        return ds_id
        
    except Exception as e:
        print(f"  Error creating data source: {e}")
        sys.exit(1)

def main():
    # Get stack name from environment or use default
    stack_name = os.environ.get('STACK_NAME', 'hr-assistant-kb-stack')
    region = os.environ.get('AWS_REGION', 'us-east-1')
    
    print("=" * 50)
    print("Bedrock Knowledge Base Setup")
    print("=" * 50)
    print()
    
    # Get stack outputs
    print("Retrieving CloudFormation stack outputs...")
    outputs = get_stack_outputs(stack_name, region)
    print("  ✓ Stack outputs retrieved")
    print(f"    Bucket: {outputs['KnowledgeBaseBucketName']}")
    print(f"    Collection: {outputs['OpenSearchCollectionEndpoint']}")
    
    # Wait a bit for collection to be fully ready
    print("\nWaiting for OpenSearch collection to be ready...")
    time.sleep(15)
    print("  ✓ Ready")
    
    # Create OpenSearch index
    index_name = create_opensearch_index(outputs['OpenSearchCollectionEndpoint'], region)
    
    # Create Knowledge Base
    kb_id = create_knowledge_base(outputs, region)
    
    # Create Data Source
    ds_id = create_data_source(kb_id, outputs['KnowledgeBaseBucketName'], region)
    
    # Save IDs for later use
    config = {
        'knowledge_base_id': kb_id,
        'data_source_id': ds_id,
        'bucket_name': outputs['KnowledgeBaseBucketName'],
        'collection_endpoint': outputs['OpenSearchCollectionEndpoint']
    }
    
    with open('kb_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n" + "=" * 50)
    print("Setup Complete!")
    print("=" * 50)
    print(f"\nKnowledge Base ID: {kb_id}")
    print(f"Data Source ID: {ds_id}")
    print(f"S3 Bucket: {outputs['KnowledgeBaseBucketName']}")
    print("\nConfiguration saved to: kb_config.json")
    print()

if __name__ == '__main__':
    main()
