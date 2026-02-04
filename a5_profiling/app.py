from fastapi import FastAPI

app = FastAPI(title="Inference Mock")

# 导入并注册路由
from .routes import infer
infer.register_routes(app)


@app.get("/healthz")
async def healthz():
    return {"ok": True}
