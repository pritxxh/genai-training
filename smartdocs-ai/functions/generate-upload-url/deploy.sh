#!/bin/bash
set -e  # stop on any error

rm -f function.zip
zip function.zip handler.py
cd .. && zip -r generate-upload-url/function.zip shared/ && cd generate-upload-url

aws lambda update-function-code \
  --function-name smartdocs-generate-upload-url \
  --zip-file fileb://function.zip \
  --region us-east-1

echo "generate-upload-url deployed!"
