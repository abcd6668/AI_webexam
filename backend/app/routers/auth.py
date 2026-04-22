from fastapi import APIRouter, HTTPException, status
from ..schemas import LoginRequest, TokenOut
from ..auth import create_access_token, verify_password, hash_password
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["认证"])

# 将初始密码 hash 一次（生产环境应存入数据库）
_hashed_admin_pw = hash_password(settings.ADMIN_PASSWORD)


@router.post("/login", response_model=TokenOut)
def login(body: LoginRequest):
    if body.username != settings.ADMIN_USERNAME or not verify_password(body.password, _hashed_admin_pw):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    token = create_access_token({"sub": body.username})
    return TokenOut(access_token=token)
