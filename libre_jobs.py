from libre_bot import *
from apscheduler.schedulers.background import BlockingScheduler

scheduler = BlockingScheduler()
scheduler.add_job(sender, 'cron', hour=15, minute=15, second=0, args=(app, ))

scheduler.start()
