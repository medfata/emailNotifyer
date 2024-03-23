from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import ALBResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
import json
import base64
import csv 


app = ALBResolver()
logger = Logger()




@app.post("/sms")
def create_todo():
    data: dict = app.current_event.json_body
    logger.info(f"Triggering post request handler with the following body: {data}")

    try:
        # Check if the 'file' key exists in the request body
        if 'file' in data:
            # Decode base64 content
            file_content = base64.b64decode(data['file']).decode('utf-8')

            # Assuming the file is JSON or CSV
            if file_content.startswith('{') and file_content.endswith('}'):
                content = json.loads(file_content)
            else:
                content = list(csv.DictReader(file_content.splitlines()))

            logger.info(f"File content: {content}")

            # Modify the response based on the loaded content
            response_body = {
                'statusCode': 200,
                'body': content,
            }
        else:
            raise ValueError("No 'file' key in the request body")
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        response_body = {
            'statusCode': 500,
            'body': 'Error processing file',
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