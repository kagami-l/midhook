import uvicorn
from fastapi import FastAPI
from midhook.app.route.gitlab_lark import router as gl_router


app = FastAPI(title="A bridge")

app.include_router(gl_router)

@app.get("/")
def hello():
    return {"hello": "world"}

if __name__ == "__main__":
    uvicorn.run("gfbot.app.app:app",host="0.0.0.0", reload=True)
