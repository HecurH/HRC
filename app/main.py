from threading import Lock
from fastapi import FastAPI

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db import DB
from mail import Mail

scheduler = AsyncIOScheduler()
app = FastAPI()

db = DB("USER", "PASSWORD", "hrc")
db.tables_check()

thread = None
thread_lock = Lock()

mail = Mail()

from api import api


@app.on_event('startup')
async def startup_jobs():
    scheduler.start()


app.include_router(api)


@scheduler.scheduled_job('interval', minutes=10)
def db_check():
    db.check_verified()


@scheduler.scheduled_job('interval', minutes=30)
def tokens_check():
    db.check_tokens()
