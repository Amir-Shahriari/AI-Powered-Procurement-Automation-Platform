# app/main.py
from fastapi import FastAPI
from .routers import upload, records, ui
from .routers import api as api_router, ui as ui_router

app = FastAPI(title="Spec → RFT + TEPP + Returnables (JSON)")
from .routers import api as api_router

app.include_router(api_router.router)
app.include_router(ui_router.router)
