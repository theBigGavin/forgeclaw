"""FastAPI 主应用."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from forgeclaw.api.routes import assets, executions, memory, planner, scheduler, skills, workflows


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理."""
    # 启动
    print("🚀 ForgeClaw starting...")
    yield
    # 关闭
    print("🛑 ForgeClaw shutting down...")


def create_app() -> FastAPI:
    """创建 FastAPI 应用."""
    app = FastAPI(
        title="ForgeClaw API",
        description="确定性 AI Agent 编排平台",
        version="0.1.0",
        lifespan=lifespan,
    )

    # 注册路由
    app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])
    app.include_router(executions.router, prefix="/api/v1/executions", tags=["executions"])
    app.include_router(skills.router, prefix="/api/v1/skills", tags=["skills"])
    app.include_router(planner.router, prefix="/api/v1/planner", tags=["planner"])
    app.include_router(memory.router, prefix="/api/v1/memory", tags=["memory"])
    app.include_router(scheduler.router, prefix="/api/v1/scheduler", tags=["scheduler"])
    app.include_router(assets.router, prefix="/api/v1/assets", tags=["assets"])

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    @app.get("/")
    async def root():
        return {
            "name": "ForgeClaw",
            "version": "0.1.0",
            "description": "确定性 AI Agent 编排平台",
        }

    return app


# 应用实例
app = create_app()
