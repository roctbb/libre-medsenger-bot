from libre_bot import *
from apscheduler.schedulers.background import BlockingScheduler

scheduler = BlockingScheduler()
scheduler.add_job(sender, 'interval', days=1, args=(app, ))

scheduler.start()
