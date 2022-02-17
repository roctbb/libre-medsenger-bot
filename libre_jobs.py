from libre_bot import *
from apscheduler.schedulers.background import BlockingScheduler
import logging

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

scheduler = BlockingScheduler()
scheduler.add_job(lambda:print("ping"), 'interval', hours=1)
scheduler.add_job(sender, 'cron', hour=9, minute=0, second=0, args=(app, ))

scheduler.start()
