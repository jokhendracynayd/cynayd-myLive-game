#PRODUCTION
from fastapi import FastAPI,BackgroundTasks
from routers.r_fruit import router as fruit_router
from routers.r_teen_patti import router as teen_patti_router
# from routers.r_new_fruit import router as new_router
from routers.r_greedy import router as greedy_router
from fastapi.exceptions import HTTPException
from config.db import db
import asyncio
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import time
app = FastAPI(debug=True)
# app.include_router(new_router,prefix='/api/new-fruit')
app.include_router(fruit_router,prefix="/api/fruit-game")
app.include_router(teen_patti_router,prefix="/api/teen-pati")
app.include_router(greedy_router,prefix="/api/greedy-game")
table_collection = db["fruits"]
table_teen_patti_collection = db["teen_pattis"]
table_greedy_collection = db["greedies"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this to your frontend's actual origin(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def task_to_schedule_for_greedy():
    while True:
        start_time = time.time()
        data = table_greedy_collection.find_one({"game_status": "active"})
        if data:
            count= data["game_last_count"]
            if count>0:
                table_greedy_collection.find_one_and_update({"game_status": "active"},{'$inc': {'game_last_count': -1}})
        # print("this is task")
        elapsed_time = time.time() - start_time
        sleep_time = max(0, 1 - elapsed_time)
        await asyncio.sleep(sleep_time)


# This is schedular for fruit game
@app.get('/')
async def home():
    return {"message":"Welcome to MyLiveGame"}

async def task_to_schedule():
    while True:
        start_time = time.time()
        data = table_collection.find_one({"game_status": "active"})
        if data:
            count= data["game_last_count"]
            if count>0:
                table_collection.find_one_and_update({"game_status": "active"},{'$inc': {'game_last_count': -1}})
        # print("this is task")
        elapsed_time = time.time() - start_time
        sleep_time = max(0, 1 - elapsed_time)
        
        await asyncio.sleep(sleep_time)


# This is schedular for teen patti

async def another_task_to_schedule():
    while True:
        data = table_teen_patti_collection.find_one({"game_status": "active"})
        if data:
            count= data["game_last_count"]
            if count>0:
                table_teen_patti_collection.find_one_and_update({"game_status": "active"},{'$inc': {'game_last_count': -1}})
        await asyncio.sleep(1.5) 


def run_scheduled_task(background_tasks: BackgroundTasks):
    background_tasks.add_task(task_to_schedule)
    background_tasks.add_task(another_task_to_schedule)
    background_tasks.add_task(task_to_schedule_for_greedy)


@app.on_event("startup")
async def startup_event():
    background_tasks = BackgroundTasks()
    background_tasks.add_task(run_scheduled_task, background_tasks)
    asyncio.create_task(task_to_schedule())  # Start the task in the background
    asyncio.create_task(another_task_to_schedule())
    asyncio.create_task(task_to_schedule_for_greedy())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
