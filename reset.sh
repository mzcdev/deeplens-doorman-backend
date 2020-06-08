#!/bin/sh

echo "aws rekognition delete-collection --collection-id ${STORAGE_NAME} --region ${AWSREGION}"
aws rekognition delete-collection --collection-id ${STORAGE_NAME} --region ${AWSREGION} | jq .

echo "aws rekognition create-collection --collection-id ${STORAGE_NAME} --region ${AWSREGION}"
aws rekognition create-collection --collection-id ${STORAGE_NAME} --region ${AWSREGION} | jq .

echo "sls deploy"
sls deploy
