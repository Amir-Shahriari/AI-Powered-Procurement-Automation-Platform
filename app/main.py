# app/main.py
from fastapi import FastAPI


app = FastAPI(title="Spec → RFT + TEPP + Returnables (JSON)")
from .routers import api as api_router

from fastapi.responses import RedirectResponse

@app.get("/")
def root():
    return RedirectResponse(url="http://localhost:8501")  
# app.include_router(api_router.router)
# app.include_router(ui_router.router)
