from aws_cdk import (
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_ses as ses,
    aws_iam as iam,
    aws_s3 as s3,
    core,
    aws_lambda_event_sources 
)

class SmsNotificationStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)



        # Define a LayerVersion for aws_lambda_powertools
        powertools_layer = _lambda.LayerVersion(
            self,
            "PowertoolsLayer",
            code=_lambda.Code.from_asset("../packages.zip"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_8],
            description="Layer containing aws_lambda_powertools"
        )
        # Create a DynamoDB table
        dynamo_table = dynamodb.Table(
            self,
            "sms_table",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            removal_policy=core.RemovalPolicy.DESTROY,
            time_to_live_attribute="ttl"
        )

        # Lambda function
        notification_lambda_function = _lambda.Function(
            self,
            "EmailNotificationLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="email_notify.handler",
            code=_lambda.Code.from_asset("../lambdas/email_notification"),
            layers=[powertools_layer],
            environment={
                "DYNAMODB_TABLE_NAME": dynamo_table.table_name            
            }
        )
        
        # Create a Lambda function
        hello_world_function = _lambda.Function(
            self,
            "HelloWorldFunction",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="hello_world.handler",
            code=_lambda.Code.from_asset("../lambdas/hello_world"),
            layers=[powertools_layer],
            environment={
                "DYNAMODB_TABLE_NAME": dynamo_table.table_name,
                "FUNCTION_NAME":  notification_lambda_function.function_name
            },
        )

        dynamo_table.grant_read_write_data(hello_world_function)
        dynamo_table.grant_read_write_data(notification_lambda_function)

        # Create an API Gateway
        api = apigateway.RestApi(
            self,
            "MyApi",
            rest_api_name="MyApi",
            description="My API Gateway",
        )

        # Create a resource and add a POST method
        sms_resource = api.root.add_resource("sms")
        sms_resource.add_method("POST", apigateway.LambdaIntegration(hello_world_function))
        # sms_with_id_resource = sms_resource.add_resource("{request_id}")
        # sms_with_id_resource.add_method("GET", apigateway.LambdaIntegration(hello_world_function))

        client_sms_requests_bucket = s3.Bucket(
            scope=self, 
            id="client_sms_requests_bucket",
            bucket_name="sms--eu-west-1") 
        
        api_gateway_role = iam.Role(scope=self, id='api_agteway_role',assumed_by=iam.ServicePrincipal('apigateway.amazonaws.com'))
        api_gateway_role.add_to_policy(iam.PolicyStatement(resources=[client_sms_requests_bucket.bucket_arn],actions=["s3:PutObject"]))
        client_sms_requests_bucket.grant_read_write(api_gateway_role)
        client_sms_requests_bucket.grant_read(hello_world_function)

        # Add S3 event trigger to Lambda
        hello_world_function.add_event_source(aws_lambda_event_sources.S3EventSource(client_sms_requests_bucket, events=[s3.EventType.OBJECT_CREATED]))

        #PutObject method
        putObjectIntegration = apigateway.AwsIntegration(
            service="s3",
            region="eu-west-1",
            path='{bucket}/{object}',
            integration_http_method="PUT",
            options= {
                "credentials_role": api_gateway_role,
                "passthrough_behavior": apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES,
                "request_parameters":{
                    "integration.request.path.bucket":"method.request.path.folder",
                    "integration.request.path.object":"method.request.path.item",
                    "integration.request.header.Accept":"method.request.header.Accept"
                },
                "integration_responses": [{
                "statusCode": '200',
                "response_parameters": { 
                    'method.response.header.Content-Type': 'integration.response.header.Content-Type',
                    "method.response.header.Access-Control-Allow-Origin": "'*'"
                    }
                }]        
            }
        )

        #PutObject method options
        putObjectMethodOptions = {
        "authorization_type": apigateway.AuthorizationType.NONE,
        "request_parameters": {
            'method.request.path.folder': True,
            'method.request.path.item': True,
            'method.request.header.Accept': True,
            'method.request.header.Content-Type': True
        },
        "method_responses": [
            {
            "statusCode": '200',
            "response_parameters": {
                'method.response.header.Content-Type': True, 
                "method.response.header.Access-Control-Allow-Origin": "'*'"
            }
            }]
        }
        sms_resource.add_resource("{folder}").add_resource("{item}").add_method(http_method="PUT", integration=putObjectIntegration,  **putObjectMethodOptions);
        
        
        notification_lambda_function.add_to_role_policy(
            statement = iam.PolicyStatement(
                actions=["ses:SendRawEmail", "ses:SendEmail"],
                resources=["*"]
            )
        )
        notification_lambda_function.grant_invoke(hello_world_function)
        ses_email_identity = ses.CfnEmailIdentity(scope=self,id="emailSender", email_identity="medfata3@gmail.com")