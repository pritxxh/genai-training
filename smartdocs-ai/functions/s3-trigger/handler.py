import json
import boto3
from datetime import datetime
from decimal import Decimal
from boto3.dynamodb.types import TypeDeserializer

s3 = boto3.client("s3")
dynamodb = boto3.client("dynamodb")

BUCKET_NAME = "smartdocs-ai-347152105990"
TABLE_NAME = "smartdocs-documents"

def lambda_handler(event, context):
    """
    Event trigger using S3 event notifications
    """
    
    try:
        # Step 1: extract bucket and key from the S3 event
        record = event["Records"][0]
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        
        # Step 2: skip non .txt files
        if not key.endswith(".txt"):
            print(f"Skipping non-txt file: {key}")
            return
        
        # Step 3: read the content of the txt file
        obj = s3.get_object(Bucket=bucket, Key=key)
        text = obj["Body"].read().decode("utf-8")
        
        # Step 4: calculate counts
        word_count = len(text.split())
        char_count = len(text)
        
        # Step 5: Save to DynamoDB — field names match the HTTP handler schema
        dynamodb.put_item(
            TableName=TABLE_NAME,
            Item={
                "doc_id": {"S": key},
                "s3_key": {"S": key},
                "word_count": {"N": str(word_count)},
                "char_count": {"N": str(char_count)},
                "timestamp": {"S": datetime.utcnow().strftime("%Y/%m/%d")}
            }
        )
        print(f"Processed {key}: {word_count} words, {char_count} chars")
        
    except Exception as e:
        print(f"Error processing {key}: {str(e)}")
        raise