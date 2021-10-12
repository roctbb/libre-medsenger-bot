from config import *
from redis import Redis
from rq import Worker, Queue, Connection
import sentry_sdk
from sentry_sdk.integrations.rq import RqIntegration

sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[RqIntegration()])

listen = ['libre']
conn = Redis()


if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()

