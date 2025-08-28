import os, logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import user as user_routes
from app.routes import data as data_routes

app = FastAPI(title="Name Match Board (users & shows, in-memory)")

logging.config.fileConfig("./logging.conf", disable_existing_loggers=False)
logger = logging.getLogger("app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_routes.router)
app.include_router(data_routes.router)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
@app.get("/")
def root():
    return {"message": "OK. Open /static/index.html for the UI."}
