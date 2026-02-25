import json

CASE_TYPES = [
    {
        'id': 'compensation',
        'name': 'Compensation',
        'description': 'Salary, bonuses, and pay-related inquiries'
    },
    {
        'id': 'benefits',
        'name': 'Benefits',
        'description': 'Health insurance, retirement, and other benefits'
    },
    {
        'id': 'pto',
        'name': 'PTO (Paid Time Off)',
        'description': 'Vacation, sick leave, and time off requests'
    },
    {
        'id': 'general',
        'name': 'General HR',
        'description': 'General HR questions and inquiries'
    },
    {
        'id': 'performance',
        'name': 'Performance Review',
        'description': 'Performance evaluations and feedback'
    },
    {
        'id': 'travel',
        'name': 'Travel & Expenses',
        'description': 'Travel reimbursement and expense reports'
    },
    {
        'id': 'workplace',
        'name': 'Workplace Issue',
        'description': 'Workplace concerns and policy questions'
    }
]

def handler(event, context):
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'case_types': CASE_TYPES
        })
    }
