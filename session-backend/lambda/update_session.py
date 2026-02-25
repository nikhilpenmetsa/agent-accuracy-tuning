import json
import boto3
import os
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def handler(event, context):
    try:
        # Extract user info from Cognito authorizer
        claims = event['requestContext']['authorizer']['claims']
        user_id = claims.get('sub')  # Use UUID (sub claim)
        
        # Get session_id from path parameters
        session_id = event['pathParameters']['session_id']
        
        # Parse request body
        body = json.loads(event['body'])
        
        # Validate that session exists and belongs to user
        existing = table.get_item(
            Key={
                'user_id': user_id,
                'session_id': session_id
            }
        )
        
        if 'Item' not in existing:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Session not found'})
            }
        
        # Build update expression
        update_expr = "SET updated_at = :updated_at"
        expr_values = {
            ':updated_at': datetime.utcnow().isoformat()
        }
        
        # Update session_title if provided
        if 'session_title' in body:
            update_expr += ", session_title = :title"
            expr_values[':title'] = body['session_title']
        
        # Update item
        response = table.update_item(
            Key={
                'user_id': user_id,
                'session_id': session_id
            },
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ReturnValues='ALL_NEW'
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps({
                'message': 'Session updated successfully',
                'session': response['Attributes']
            }, cls=DecimalEncoder)
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
