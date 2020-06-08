#!/bin/sh

aws rekognition delete-collection --collection-id ${STORAGE_NAME} --region ${AWSREGION} | jq .

aws rekognition create-collection --collection-id ${STORAGE_NAME} --region ${AWSREGION} | jq .

sls deploy
