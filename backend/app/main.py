from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from .models import Base
from .routers import auth, admin, exam

# 建表（首次启动自动创建）
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="在线考试系统 API",
    version="1.0.0",
    description="提供试卷管理、考生答题、自动判分功能",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 生产环境改为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(exam.router)


@app.get("/", tags=["健康检查"])
def root():
    return {"status": "ok", "message": "在线考试系统运行中"}
