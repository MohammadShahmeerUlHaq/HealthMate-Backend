import routes
import models
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from tasks.scheduler import start_scheduler

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_headers=["*"],
    allow_origins=["*"],
    allow_methods=["*"],
    allow_credentials=True,
)

Base.metadata.create_all(bind=engine)

app.include_router(routes.router)
start_scheduler()