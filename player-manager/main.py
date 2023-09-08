import json

def main_handler(event, context):
    try:
        print(event) # Print event, you can find how event constructed
        path = event.get('path') # Get path
        res_msg = "Path '%s' not registered." % path
        response = {'statusCode': 404, 'body': json.dumps({"msg": res_msg})}

        event_body = event.get('body')
        event_body = json.loads(event_body if event_body is not None else '{}')

        if path == "/create_user":
            response = {'statusCode': 200, 'body': json.dumps({"msg": "create user success"})}
            return response

        return response
    except Exception as err:
        return {'statusCode': 500}

