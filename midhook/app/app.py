import uvicorn
from fastapi import FastAPI

from midhook.app.route.gitlab import router as gl_router
from midhook.app.route.lark import router as lk_router

app = FastAPI(title="A bridge")

app.include_router(gl_router)
app.include_router(lk_router)


@app.get("/")
def hello():
    return {"hello": "world"}


if __name__ == "__main__":
    uvicorn.run("midhook.app.app:app", host="0.0.0.0", reload=True)
