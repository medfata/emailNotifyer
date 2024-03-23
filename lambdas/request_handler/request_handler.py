from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import ALBResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, CORSConfig
import json
import boto3
import os
from uuid import uuid4
import time 

#the allow_origin url is set to 'http://localhost:5173'  just for my local frontend app 
cors_config = CORSConfig(allow_origin="http://localhost:5173", max_age=300)
app = APIGatewayRestResolver(cors=cors_config)


logger = Logger()

dynamodb = boto3.resource("dynamodb")
lambda_client = boto3.client('lambda')
s3_client = boto3.client('s3')
#ssm =  boto3.client("ssm")
target_function_name = os.environ.get("FUNCTION_NAME")

@app.post("/sms")
def create_request():
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
        # Invoke the Lambda function asynchronously
        logger.info(f"invoking {target_function_name} lambda function", payload=body)
        response = lambda_client.invoke(
            FunctionName= target_function_name,
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps(body)
        )
        logger.info(f"lambda function response: {response}")
        # Modify the response based on the loaded content
        response_body = {"request_id": body["id"]}
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        response_body = {
            'statusCode': 500,
            'body': 'Error processing request',
        }

    return response_body

@app.get("/sms/<requrest_id>")
def get_request(requrest_id:str):
    if not requrest_id:
        return {
                'statusCode': 400,
                'body': f"request_id param is required !",
            }
    logger.info(f"get request for requestId: {requrest_id}")
    dynamodb_table_name = os.environ.get("DYNAMODB_TABLE_NAME")
    # Save the request body to DynamoDB
    table = dynamodb.Table(dynamodb_table_name)
    try:
        response = table.get_item(
            Key={
                'id': requrest_id
            }
        )
        # Check if the item was found
        item = response.get('Item')
        if item:
            return {
                'statusCode': 200,
                'body': item
            }
        else:
            return {
                'statusCode': 404,
                'body': f"Item with requestId {requrest_id} not found"
            }

    except Exception as e:
        logger.error(f"Error retrieving data from DynamoDB: {e}")
        return {
            'statusCode': 500,
            'body': "Internal Server Error"
        }


def is_an_s3_event(event):
    return 'Records' in event and len(event['Records']) > 0 and 's3' in event['Records'][0]

def handler(event, context):
    # Log the incoming event
    logger.info(f"Received event: {json.dumps(event)}")
    if is_an_s3_event(event):
        s3_event = event['Records'][0]['s3']
        object_key = s3_event['object']['key']
        bucket_name = s3_event['bucket']['name']
        logger.info(f"get object with key: {object_key}, from bucket_name: {bucket_name}")
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        file_content = response['Body'].read().decode('utf-8')
        body = json.loads(file_content)
        dynamodb_table_name = os.environ.get("DYNAMODB_TABLE_NAME")
        # Save the request body to DynamoDB
        table = dynamodb.Table(dynamodb_table_name)
        body["id"] = str(uuid4())
        # Calculate the expiration time (30 minutes from now)
        ttl_minutes = 30
        expiration_time_seconds = int(time.time()) + (ttl_minutes * 60)
        body["ttl"] = expiration_time_seconds
        table.put_item(Item=body)
        # Invoke the Lambda function asynchronously
        logger.info(f"invoking {target_function_name} lambda function", payload=body)
        response = lambda_client.invoke(
            FunctionName= target_function_name,
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps(body)
        )
        logger.info(f"lambda function response: {response}")
        return
    return app.resolve(event, context)