from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import ALBResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
import json
import boto3
import os
from uuid import uuid4
import time 

app = ALBResolver()
logger = Logger()

dynamodb = boto3.resource("dynamodb")
#ssm =  boto3.client("ssm")

@app.post("/sms")
def create_todo():
    body: dict = app.current_event.json_body
    logger.info(f"Triggering post request handler with the following body: {body}")

    try:
        if 'message' not in body or 'email_list' not in body:
            raise ValueError("No 'message' or 'email_list' on the request body!")
        #table_name_parameter = os.environ.get('DYNAMODB_TABLE_PARAMETER_NAME')
        #dynamodb_table_name = ssm.get_parameter(Name=table_name_parameter)['Parameter']['Value']
        dynamodb_table_name = os.environ.get("DYNAMODB_TABLE_NAME")
        # Save the request body to DynamoDB
        table = dynamodb.Table(dynamodb_table_name)
        body["id"] = str(uuid4())
        # Calculate the expiration time (30 minutes from now)
        ttl_minutes = 30
        expiration_time_seconds = int(time.time()) + (ttl_minutes * 60)
        body["ttl"] = expiration_time_seconds
        table.put_item(Item=body)
        # Modify the response based on the loaded content
        response_body = {
            'statusCode': 200,
            'body':body["id"]
        }
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        response_body = {
            'statusCode': 500,
            'body': 'Error processing request',
        }

    return response_body

@app.get("/sms")
def get_todos():
    logger.info(f"triggering get request")
    # Returns the created todo object, with a HTTP 201 Created status
    return {
        'statusCode': 200,
        'body': 'Hello, World!',
    }

def handler(event, context):
    # Log the incoming event
    logger.info(f"Received event: {json.dumps(event)}")
    return app.resolve(event, context)