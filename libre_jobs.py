from libre_bot import *
from apscheduler.schedulers.background import BlockingScheduler

scheduler = BlockingScheduler()
scheduler.add_job(sender, 'cron', hour=16, minute=12, second=0, args=(app, ))

scheduler.start()
