#!/bin/bash
zip function.zip handler.py
aws lambda update-function-code \
  --function-name smartdocs-s3-notification-event-trigger \
  --zip-file fileb://function.zip \
  --region us-east-1
echo "s3-notification-event-trigger deployed!"
