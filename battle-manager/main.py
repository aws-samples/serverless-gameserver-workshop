import json

def main_handler(event, context):
    try:
        # Validate request parameters
        route_key = event.get('requestContext', {}).get('routeKey')
        connection_id = event.get('requestContext', {}).get('connectionId')
        event_body = event.get('body')
        event_body = json.loads(event_body if event_body is not None else '{}')

        if route_key is None or connection_id is None:
            return {'statusCode': 400}

        if route_key == 'attack':
            print('test attack')
            return {'statusCode': 200}

        if route_key == 'die':
            print('test die')
            return {'statusCode': 200}

        if route_key == 'syncscore':
            print('test syncscore')
            return {'statusCode': 200}

    except Exception as err:
        print(err)
        return {'statusCode': 500}

