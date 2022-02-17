from config import *
from redis import Redis
import sentry_sdk
import json
from manage import *
from libre_api import create_client, register_user, send_reports


if __name__ == '__main__':
    with app.app_context():
        print("queue started...")

        browser = create_client()
        conn = Redis()

        channel = 'libre'
        p = conn.pubsub()
        p.subscribe(channel)

        while True:
            message = p.get_message()
            if message and not message['data'] == 1:
                try:
                    print("QUEUE: got task")
                    message = message['data'].decode('utf-8')
                    print(message)
                    payload = json.loads(message)

                    if payload['cmd'] == "register":
                        register_user(payload['id'], browser)
                    if payload['cmd'] == "report":
                        send_reports(payload['ids'], browser)

                    print("QUEUE: task ready")
                except Exception as e:
                    print("QUEUE: task error")
                    print(e)



