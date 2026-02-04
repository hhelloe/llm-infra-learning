from fastapi import FastAPI

# 创建 factory 函数，用于 uvicorn --factory 加载
def create_app():
    app = FastAPI(title="Inference Mock")

    # 导入并注册路由
    from routes import infer
    infer.register_routes(app)

    @app.get("/healthz")
    async def healthz():
        return {"ok": True}

    return app

# 保持直接导入方式的兼容性
app = create_app()
