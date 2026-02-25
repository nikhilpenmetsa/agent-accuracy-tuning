import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def handler(event, context):
    try:
        # Extract user info from Cognito authorizer
        claims = event['requestContext']['authorizer']['claims']
        user_id = claims.get('sub')  # Use UUID (sub claim)
        
        # Get session_id from path parameters
        session_id = event['pathParameters']['session_id']
        
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
        
        # Delete session
        table.delete_item(
            Key={
                'user_id': user_id,
                'session_id': session_id
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps({
                'message': 'Session deleted successfully',
                'session_id': session_id
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
