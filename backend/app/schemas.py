from datetime import datetime
from pydantic import BaseModel, Field


# ===== 题目 =====
class OptionSchema(BaseModel):
    key: str
    text: str


class QuestionCreate(BaseModel):
    type: str  # single | multiple | judge | subjective
    content: str
    score: float = 5.0
    options: list[OptionSchema] = []
    answer: str = ""        # 标准答案
    max_length: int = 1000  # 主观题最大字数
    order_index: int = 0


class QuestionOut(QuestionCreate):
    id: int
    exam_id: int

    model_config = {"from_attributes": True}


class QuestionOutNoAnswer(BaseModel):
    """考生端：不暴露答案"""
    id: int
    exam_id: int
    type: str
    content: str
    score: float
    options: list[OptionSchema]
    max_length: int
    order_index: int

    model_config = {"from_attributes": True}


# ===== 试卷 =====
class ExamCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: str = ""
    duration: int = 0   # 秒，0=不限时
    is_active: bool = True


class ExamUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    duration: int | None = None
    is_active: bool | None = None


class ExamOut(BaseModel):
    id: int
    title: str
    description: str
    duration: int
    is_active: bool
    created_at: datetime
    questions: list[QuestionOut] = []

    model_config = {"from_attributes": True}


class ExamPublic(BaseModel):
    """考生端：不含答案"""
    id: int
    title: str
    description: str
    duration: int
    questions: list[QuestionOutNoAnswer] = []

    model_config = {"from_attributes": True}


# ===== 提交 =====
class AnswerIn(BaseModel):
    questionId: int
    type: str
    answer: str


class SubmitRequest(BaseModel):
    examId: int
    studentName: str = Field(..., min_length=1, max_length=50)
    studentId: str = ""
    submitTime: str = ""
    answers: list[AnswerIn]


class AnswerOut(BaseModel):
    id: int
    question_id: int
    answer: str
    is_correct: bool | None
    score_got: float

    model_config = {"from_attributes": True}


class SubmissionOut(BaseModel):
    id: int
    exam_id: int
    student_name: str
    student_id: str
    submitted_at: datetime
    auto_score: float
    total_auto_score: float
    answers: list[AnswerOut] = []

    model_config = {"from_attributes": True}


# ===== 认证 =====
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
