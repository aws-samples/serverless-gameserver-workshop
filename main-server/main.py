import json
import random
import string
import boto3

# main_server corresponds to Resources -> MainServerTable -> Properties -> TableName in template.yaml
main_server_table = boto3.resource('dynamodb').Table("main_server")

def main_handler(event, context):
    try:
        print(event)
        # get routeKey
        route_key = event.get('requestContext', {}).get('routeKey')

        # Get connectionId，for each WebSocket connection，API Gateway will assign a connectionId
        # connectionId is used for communication between client and server
        connection_id = event.get('requestContext', {}).get('connectionId')
        event_body = event.get('body')
        event_body = json.loads(event_body if event_body is not None else '{}')

        if route_key is None or connection_id is None:
            return {'statusCode': 400, 'body': 'routeKey or connectionId is None'}

        # Handle on connect
        if route_key == '$connect':
            # if connectionId is not included in the query string, generate a random one
            tmp_guest_user_id = ''.join(random.choices(string.ascii_uppercase+string.digits, k=12))
            user_id = event.get('queryStringParameters', {'user_id': tmp_guest_user_id}).get('user_id')
            main_server_table.put_item(Item={'user_id': user_id, 'connection_id': connection_id})
            print(f"connect user_id: {user_id}, connection_id: {connection_id}") # print user_id and connection_id, so we can find that in CloudWatch Log
            return {'statusCode': 200}

        # Handle on disconnect
        elif route_key == '$disconnect':
            main_server_table.delete_item(Key={'connection_id': connection_id})
            print(f"disconnect connection_id: {connection_id}") 
            return {'statusCode': 200}
        else:
            print("routeKey '%s' not registered" % event_body["action"])
            return {'statusCode': 400}

    except Exception as err:
        print(err)
        return {'statusCode': 500}

