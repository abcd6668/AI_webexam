import json
from datetime import datetime
from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    duration: Mapped[int] = mapped_column(Integer, default=0)  # 秒，0=不限时
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    questions: Mapped[list["Question"]] = relationship(
        "Question", back_populates="exam", cascade="all, delete-orphan",
        order_by="Question.order_index"
    )
    submissions: Mapped[list["Submission"]] = relationship(
        "Submission", back_populates="exam", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"))
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    type: Mapped[str] = mapped_column(String(20))   # single|multiple|judge|subjective
    content: Mapped[str] = mapped_column(Text)
    score: Mapped[float] = mapped_column(Float, default=5.0)
    # 选项存为 JSON 字符串：[{"key":"A","text":"..."}]
    options_json: Mapped[str] = mapped_column(Text, default="[]")
    # 答案存为字符串：单选"A"，多选"A,C"，判断"true"/"false"，主观题留空
    answer: Mapped[str] = mapped_column(Text, default="")
    max_length: Mapped[int] = mapped_column(Integer, default=1000)

    exam: Mapped["Exam"] = relationship("Exam", back_populates="questions")

    @property
    def options(self) -> list[dict]:
        return json.loads(self.options_json or "[]")

    @options.setter
    def options(self, value: list[dict]) -> None:
        self.options_json = json.dumps(value, ensure_ascii=False)


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"))
    student_name: Mapped[str] = mapped_column(String(50))
    student_id: Mapped[str] = mapped_column(String(50), default="")
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # 自动判分结果（主观题不计入）
    auto_score: Mapped[float] = mapped_column(Float, default=0.0)
    total_auto_score: Mapped[float] = mapped_column(Float, default=0.0)  # 可自动判分的满分

    exam: Mapped["Exam"] = relationship("Exam", back_populates="submissions")
    answers: Mapped[list["Answer"]] = relationship(
        "Answer", back_populates="submission", cascade="all, delete-orphan"
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    answer: Mapped[str] = mapped_column(Text, default="")
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # 主观题为 None
    score_got: Mapped[float] = mapped_column(Float, default=0.0)

    submission: Mapped["Submission"] = relationship("Submission", back_populates="answers")
    question: Mapped["Question"] = relationship("Question")
