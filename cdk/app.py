#!/usr/bin/env python3

from aws_cdk import core

from sms_notification_stack import SmsNotificationStack


app = core.App()
SmsNotificationStack(app, "SmsNotificationStack")
app.synth()