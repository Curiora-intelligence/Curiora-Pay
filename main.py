from fastapi import FastAPI,staticfiles
import routers.authentication as authentication,routers.dashboard as dashboard
import os
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(title="saiganesh",version="0.139.0")
app.mount("/static", staticfiles.StaticFiles(directory="static"), name="static")
load_dotenv()
app.add_middleware(SessionMiddleware,secret_key=os.getenv("secret_key"))

# HOME ROUTE
app.include_router(authentication.auth_router) # Include the auth_router from routers/authentication.py

# DASHBOARD ROUTE
app.include_router(dashboard.dashboard_router) # Include the dashboard_router from routers/dashboard.py
print(a:=10==10)