import boto3
from config.config import config

AWS_REGION = config['aws_region']
SNS_TOPIC_ARN = config['sns_topic_arn']

# AWS SNS client
sns_client = boto3.client('sns', region_name=AWS_REGION)


def send_sns_notification(subject, message):
    # print(f"Notify message: {message}")
    # pass
    sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=message,
        Subject=subject
    )
