import json
import boto3
import os

main_server_table = boto3.resource('dynamodb').Table('main_server')
common_resources_table = boto3.resource('dynamodb').Table('common_resources')

# Get main_server_api_url from environment variables
main_server_api_url_prefix = os.environ['MainServerAPIUrlPrefix']
region = os.environ['AWS_REGION']
main_server_api_url = f"https://{main_server_api_url_prefix}.execute-api.{region}.amazonaws.com/dev"

# get user_id from connection_id
def getUserIDFromConnID(connection_id):
    item_response = main_server_table.get_item(Key={'connection_id': connection_id})
    if 'Item' in item_response:
        user_id = item_response['Item']['user_id']
    else:
        user_id = None
    return user_id

# get connection_id from user_id
# we use iteration here, you should use indexes in your production environment for better performance
def getConnIDFromUserID(user_id):
    connection_ids = []
    scan_response = main_server_table.scan(ProjectionExpression='connection_id')
    connection_ids = [item['connection_id'] for item in scan_response['Items']]
    for connection_id in connection_ids:
        if getUserIDFromConnID(connection_id) == user_id:
            return connection_id
    print(f"Cannot get connection_id, user_id={user_id}")
    return -1

# Send data to client by APIGatewayManagementAPI
# WSS_SERVER is the domain of APIGateway
def server_response(connection_id, message):
    apig_management_client = boto3.client('apigatewaymanagementapi',endpoint_url=main_server_api_url)
    send_response = apig_management_client.post_to_connection(Data=message, ConnectionId=connection_id)

# Create room
def createRoom(user_id):
    room_name = "%s_ROOM" % user_id

    # Init room info
    players_in_room = [user_id]

    # currently available rooms and players in the room
    common_resources_table.put_item(Item={'resource_name': 'available_rooms', 'room_names': [room_name]})
    common_resources_table.put_item(Item={'resource_name': room_name, 'players_in_room': players_in_room})

    # index for a certain player in which room
    player_room_key = "%s_in_room" % user_id
    common_resources_table.put_item(Item={'resource_name': player_room_key, 'room_name': room_name})
    print("User created room. user_id=%s, room_name=%s." % (user_id, room_name))
    return room_name

# join other's room
def joinOthersRoom(user_id, room_name):
    # update room info
    item_response = common_resources_table.get_item(Key={'resource_name': room_name})
    players_in_room = item_response['Item']['players_in_room']
    peer_player_id = players_in_room[0]
    players_in_room.append(user_id)
    common_resources_table.put_item(Item={'resource_name': room_name, 'players_in_room': players_in_room})

    # index for a certain player in which room
    player_room_key = "%s_in_room" % user_id
    common_resources_table.put_item(Item={'resource_name': player_room_key, 'room_name': room_name})
    print("User joined other's room. user_id=%s, room_name=%s." % (user_id, room_name))
    return peer_player_id

def main_handler(event, context):
    try:
        # Validate request parameters
        route_key = event.get('requestContext', {}).get('routeKey')
        connection_id = event.get('requestContext', {}).get('connectionId')
        event_body = event.get('body')
        event_body = json.loads(event_body if event_body is not None else '{}')

        if route_key is None or connection_id is None:
            return {'statusCode': 400}

        if route_key == 'joinroom':
            user_id = getUserIDFromConnID(connection_id)
            # When a new player joins, check available rooms first, if there is one, join, if not, create a new room
            item_response = common_resources_table.get_item(Key={'resource_name': 'available_rooms'})
            room_name = ""
            peer_player_id = ""

            if 'Item' in item_response:
                room_names = item_response['Item']['room_names']
                # create a new room if there is no available room
                if len(room_names) == 0:
                    room_name = createRoom(user_id)
                else:
                    room_name = room_names.pop()
                    peer_player_id = joinOthersRoom(user_id, room_name)
                    # finish matchmaking, update available rooms list
                    common_resources_table.put_item(Item={'resource_name': 'available_rooms', 'room_names': room_names})
            # create a new room if there is no available room
            else:
                room_name = createRoom(user_id)

            # response json data to client after joining room
            message = '{"action":"joinroom", "data":"%s"}' % room_name
            server_response(connection_id, message)
            # notify both players peer_player_id
            if peer_player_id != "":
                message = '{"action":"peer_player_id", "data":"%s"}' % peer_player_id
                server_response(connection_id, message)

                peer_connection_id = getConnIDFromUserID(peer_player_id)
                message = '{"action":"peer_player_id", "data":"%s"}' % user_id
                server_response(peer_connection_id, message)

            return {'statusCode': 200}

        if route_key == 'exitroom':
            print('test exitroom')
            return {'statusCode': 200}

        if route_key == 'destroyroom':
            print('test destroyroom')
            return {'statusCode': 200}

    except Exception as err:
        print(err)
        return {'statusCode': 500}

