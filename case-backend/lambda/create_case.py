import json
import boto3
import os
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def handler(event, context):
    try:
        # Extract user info from Cognito authorizer
        claims = event['requestContext']['authorizer']['claims']
        user_id = claims.get('sub')  # Use UUID (sub claim)
        email = claims.get('email')  # Keep email for display
        
        # Parse request body
        body = json.loads(event['body'])
        
        # Validate required fields
        if 'case_type' not in body or 'description' not in body:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'case_type and description are required'})
            }
        
        # Create case
        case_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        case_item = {
            'case_id': case_id,
            'employee_id': user_id,  # Use UUID
            'employee_email': email,  # Store email for display
            'case_type': body['case_type'],
            'description': body['description'],
            'status': 'open',
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        # Add session_id if provided (optional field)
        if 'session_id' in body:
            case_item['session_id'] = body['session_id']
        
        # Store in DynamoDB
        table.put_item(Item=case_item)
        
        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Case created successfully',
                'case': case_item
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }
