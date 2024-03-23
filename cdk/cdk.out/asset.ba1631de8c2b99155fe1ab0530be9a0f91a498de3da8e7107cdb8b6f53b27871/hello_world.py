from aws_lambda_powertools import Logger
import json

logger = Logger()


def handler(event, context):
    # Log the incoming event
    logger.info(f"Received event: {json.dumps(event)}")

    # Your business logic here
    response_body = 'Hello, World!'

    return {
        'statusCode': 200,
        'body': response_body,
    }