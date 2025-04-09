from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

def start_scheduler():
    scheduler.start()

def shutdown_scheduler():
    scheduler.shutdown()
