from aws_lambda_powertools import Logger
import json

from aws_lambda_powertools.event_handler import ALBResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

app = ALBResolver()
logger = Logger()




@app.post("/sms")
def create_todo():
    data: dict = app.current_event.json_body
    logger.info(f"triggering post request handler with the following body: {data}")
    # Returns the created todo object, with a HTTP 201 Created status
    return {
        'statusCode': 200,
        'body': 'Hello, World!',
    }

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