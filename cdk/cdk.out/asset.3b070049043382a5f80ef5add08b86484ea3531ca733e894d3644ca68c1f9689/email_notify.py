import json 
import boto3
from aws_lambda_powertools import Logger
import os 

logger = Logger()

ses_client = boto3.client("ses", region_name="eu-west-1")
dynamodb = boto3.resource("dynamodb")
dynamodb_table_name = os.environ.get("DYNAMODB_TABLE_NAME")
def handler(event, context):
    logger.info(f"lambda event: {event}")
    requrest_id = event["id"]
    subject = f"subject with request_id: {requrest_id}"
    body = event["message"]  
    message = {"Subject": {"Data": subject}, "Body": {"Html": {"Data": body}}} 
    request_status = ""
    try:
        response = ses_client.send_email(Source= "medfata3@gmail.com",
                                Destination= {"ToAddresses": event["email_list"]}, Message = message)
        request_status = "Done"
    except Exception as e:
        logger.error(f"error while sending emails: {e}")
        request_status = "Error"
    logger.info(f"ses response: {response}")
    try:
        table = dynamodb.Table(dynamodb_table_name)
        # Update the item by ID
        db_response = table.update_item(
            Key={
                'id': requrest_id
            },
            UpdateExpression='SET #statusAttr = :statusVal',
            ExpressionAttributeNames={
                '#statusAttr': 'status'
            },
            ExpressionAttributeValues={
                ':statusVal': request_status
            },
            ReturnValues='UPDATED_NEW'
        )
        updated_item = db_response.get('Attributes')
        logger.info(f"Updated item: {updated_item}")
    except Exception as e:
        logger.error(f"error while updating {dynamodb_table_name} item, with id: {requrest_id}")
    