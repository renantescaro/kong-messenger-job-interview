from fastapi import FastAPI

app = FastAPI(
    title="Kong Messeger Job Interview",
    version="1.0.0",
)

from main.routes import router
app.include_router(router)
