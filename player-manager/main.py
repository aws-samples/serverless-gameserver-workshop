import json
import boto3

# Get DynamoDB resource with boto3.resource('dynamodb').
# player_info represents the table name, which corresponds to Resources -> PlayerInfoTable -> Properties -> TableName in template.yaml
player_info_table = boto3.resource('dynamodb').Table("player_info")

# check if the user_id exists
def getUserInfo(user_id):
    response = player_info_table.get_item(Key={"user_id": user_id})
    if "Item" in response:
        return response["Item"]
    else:
        return None

def main_handler(event, context):
    try:
        print(event)
        path = event.get('path')
        method = event.get('httpMethod')
        event_body = event.get('body')
        event_body = json.loads(event_body if event_body is not None else '{}') # convert body to dict
        if path == "/create_user":
            if method == "POST":
                if "user_id" in event_body and event_body["user_id"] != "":
                    if getUserInfo(event_body["user_id"]) == None:
                        player_info_table.put_item(Item={"user_id": event_body["user_id"]})
                        return { 'statusCode': 200, 'body': json.dumps({"msg": "create user success"}), }
                    else:
                        return { 'statusCode': 400, 'body': json.dumps({"msg": "user_id exists"}), }
                else:
                    return { 'statusCode': 400, 'body': json.dumps({"msg": "empty user_id"}), }
    except Exception as err:
        print(err)
        return { 'statusCode': 500, 'body': json.dumps({"msg": str(err)}) }
