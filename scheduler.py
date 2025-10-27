import schedule
import time
from main import run_main
from sp500_sector import run_sp500_update
import pytz
from datetime import datetime

def job_sp500():
    print("Running sp500_sector.py...")
    run_sp500_update()

def job_main():
    print("Running main.py...")
    run_main()

taipei_tz = pytz.timezone("Asia/Taipei")

# schedule.every(1).minutes.do(job_sp500)
# schedule.every(5).minutes.do(job_main)
schedule.every().day.at("07:00", taipei_tz).do(job_sp500)
schedule.every().monday.at("06:30", taipei_tz).do(job_main)
print("Scheduler started. Press Ctrl+C to exit.")

while True:
    schedule.run_pending()
    time.sleep(1)