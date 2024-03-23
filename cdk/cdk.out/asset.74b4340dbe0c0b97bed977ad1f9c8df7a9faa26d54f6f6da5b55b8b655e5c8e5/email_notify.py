import json 
import boto3


ses_client = boto3.client("ses")

def lambda_handler(event, context):
    subject = "test subject from SMSNotificator"
    body = "test subject from SMSNotificator"  
    message = {"Subject": {"Data": subject, "Body": {"Html": {"Data": body}}}}
    response = ses_client.send_email(Source= "medfata3@gmail.com",
                                    Destination= {"ToAddresses": ["med3fata@gmail.com"]}, Message = message)
    return response