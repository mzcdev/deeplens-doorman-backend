import boto3
import hashlib
import json
import os
import requests
import time

aws_region = os.environ["AWSREGION"]
slack_channel_id = os.environ["SLACK_CHANNEL_ID"]
slack_token = os.environ["SLACK_API_TOKEN"]
storage_name = os.environ["STORAGE_NAME"]
table_name = os.environ["TABLE_NAME"]


def index_faces(key, image_id):
    try:
        client = boto3.client("rekognition", region_name=aws_region)
        res = client.index_faces(
            CollectionId=storage_name,
            Image={"S3Object": {"Bucket": storage_name, "Name": key,}},
            ExternalImageId=image_id,
            DetectionAttributes=["DEFAULT"],
        )
    except Exception as ex:
        print("Error:", ex, key)
        res = []

    print("index_faces", res)

    return res


def create_faces(user_name, real_name, image_key, image_url):
    dynamodb = boto3.resource("dynamodb", region_name=aws_region)
    table = dynamodb.Table(table_name)

    user_id = hashlib.md5(image_key.encode("utf-8")).hexdigest()
    latest = int(round(time.time() * 1000))

    try:
        res = table.put_item(
            Item={
                "user_id": user_id,
                "user_name": user_name,
                "real_name": real_name,
                "image_key": image_key,
                "image_url": image_url,
                "image_type": "unknown",
                "latest": latest,
            }
        )
    except Exception as ex:
        print("Error:", ex, user_id)
        res = []

    print("create_faces", res)

    return user_id, res


def put_faces(user_id, image_key, image_url):
    dynamodb = boto3.resource("dynamodb", region_name=aws_region)
    table = dynamodb.Table(table_name)

    latest = int(round(time.time() * 1000))

    try:
        res = table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="set image_key=:image_key, image_url=:image_url, latest=:latest",
            ExpressionAttributeValues={
                ":image_key": image_key,
                ":image_url": image_url,
                ":latest": latest,
            },
            ReturnValues="UPDATED_NEW",
        )
    except Exception as ex:
        print("Error:", ex, user_id)
        res = []

    print("put_faces", res)

    return res


def unknown(event, context):
    key = event["Records"][0]["s3"]["object"]["key"]
    # event_bucket_name = event["Records"][0]["s3"]["bucket"]["name"]

    print("Unknown", key)

    keys = key.split("/")

    auth = "Bearer {}".format(slack_token)

    text = "I don't know who this is, can you tell me?"
    image_url = "https://{}.s3-{}.amazonaws.com/{}".format(
        storage_name, aws_region, key
    )

    if len(keys) > 2:
        user_id = keys[1]

        put_faces(user_id, key, image_url)

    else:
        user_id, res = create_faces("unknown", "Unknown", key, image_url)

        index_faces(key, user_id)

    message = {
        "channel": slack_channel_id,
        "text": text,
        "attachments": [
            {
                "image_url": image_url,
                "fallback": "Nope?",
                "attachment_type": "default",
                "callback_id": user_id,
                "actions": [
                    {
                        "name": "username",
                        "text": "Select a username...",
                        "type": "select",
                        "data_source": "users",
                    },
                    # {
                    #     "name": "discard",
                    #     "text": "Ignore",
                    #     "style": "danger",
                    #     "type": "button",
                    #     "value": "ignore",
                    #     # "confirm": {
                    #     #     "title": "Are you sure?",
                    #     #     "text": "Are you sure you want to ignore and delete this image?",
                    #     #     "ok_text": "Yes",
                    #     #     "dismiss_text": "No",
                    #     # },
                    # },
                ],
            },
        ],
    }
    # print(message)
    res = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={
            "Content-Type": "application/json;charset=UTF-8",
            "Authorization": auth,
        },
        json=message,
    )
    print(res.json())

    return {}
