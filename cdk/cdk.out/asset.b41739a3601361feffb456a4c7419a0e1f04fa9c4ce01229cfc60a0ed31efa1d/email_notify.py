import json 
import boto3
from aws_lambda_powertools import Logger

logger = Logger()

ses_client = boto3.client("ses", region_name="eu-west-1")

def handler(event, context):
    logger.info(f"lambda event: {event}")

    subject = "test subject from SMSNotificator"
    body = event["message"]  
    message = {"Subject": {"Data": subject}, "Body": {"Html": {"Data": body}}} 
    response = ses_client.send_email(Source= "medfata3@gmail.com",
                                    Destination= {"ToAddresses": event["email_list"]}, Message = message)
    logger.info(f"ses response: {response}")
    return response