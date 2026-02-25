import json
import boto3
import os
import uuid
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def handler(event, context):
    try:
        # Extract user info from Cognito authorizer
        claims = event['requestContext']['authorizer']['claims']
        user_id = claims.get('sub')  # Use UUID (sub claim)
        email = claims.get('email')  # Keep email for display
        
        # Parse request body
        body = json.loads(event['body']) if event.get('body') else {}
        
        # Generate session ID (timestamp-based UUID for sorting)
        timestamp = datetime.utcnow()
        session_id = f"{timestamp.strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
        
        # Get session title from request or use default
        session_title = body.get('session_title', 'New conversation')
        
        # Create session item
        session_item = {
            'user_id': user_id,  # UUID
            'user_email': email,  # Store email for display
            'session_id': session_id,
            'session_title': session_title,
            'created_at': timestamp.isoformat(),
            'updated_at': timestamp.isoformat()
        }
        
        # Store in DynamoDB
        table.put_item(Item=session_item)
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps({
                'message': 'Session created successfully',
                'session': session_item
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Internal server error'})
        }
