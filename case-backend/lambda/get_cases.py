import json
import boto3
import os
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def handler(event, context):
    try:
        # Extract user info from Cognito authorizer
        claims = event['requestContext']['authorizer']['claims']
        user_id = claims.get('sub')  # Use UUID (sub claim)
        
        # Query cases for this employee
        response = table.query(
            IndexName='employee-index',
            KeyConditionExpression=Key('employee_id').eq(user_id)
        )
        
        cases = response.get('Items', [])
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'cases': cases,
                'count': len(cases)
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }
