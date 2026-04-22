"""管理员接口：试卷 CRUD、题目管理、查看答卷"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Exam, Question, Submission
from ..schemas import (
    ExamCreate, ExamOut, ExamUpdate,
    QuestionCreate, QuestionOut,
    SubmissionOut,
)
from ..auth import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["管理员"], dependencies=[Depends(get_current_admin)])


# ===== 试卷 =====
@router.get("/exams", response_model=list[ExamOut])
def list_exams(db: Session = Depends(get_db)):
    return db.query(Exam).order_by(Exam.created_at.desc()).all()


@router.post("/exams", response_model=ExamOut, status_code=201)
def create_exam(body: ExamCreate, db: Session = Depends(get_db)):
    exam = Exam(**body.model_dump())
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam


@router.get("/exams/{exam_id}", response_model=ExamOut)
def get_exam(exam_id: int, db: Session = Depends(get_db)):
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(404, "试卷不存在")
    return exam


@router.patch("/exams/{exam_id}", response_model=ExamOut)
def update_exam(exam_id: int, body: ExamUpdate, db: Session = Depends(get_db)):
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(404, "试卷不存在")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(exam, field, value)
    db.commit()
    db.refresh(exam)
    return exam


@router.delete("/exams/{exam_id}", status_code=204)
def delete_exam(exam_id: int, db: Session = Depends(get_db)):
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(404, "试卷不存在")
    db.delete(exam)
    db.commit()


# ===== 题目 =====
@router.get("/exams/{exam_id}/questions", response_model=list[QuestionOut])
def list_questions(exam_id: int, db: Session = Depends(get_db)):
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(404, "试卷不存在")
    return exam.questions


@router.post("/exams/{exam_id}/questions", response_model=QuestionOut, status_code=201)
def add_question(exam_id: int, body: QuestionCreate, db: Session = Depends(get_db)):
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(404, "试卷不存在")
    data = body.model_dump()
    options = data.pop("options", [])
    q = Question(**data, exam_id=exam_id)
    q.options = options
    db.add(q)
    db.commit()
    db.refresh(q)
    return _question_out(q)


@router.put("/exams/{exam_id}/questions/{q_id}", response_model=QuestionOut)
def update_question(exam_id: int, q_id: int, body: QuestionCreate, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == q_id, Question.exam_id == exam_id).first()
    if not q:
        raise HTTPException(404, "题目不存在")
    data = body.model_dump()
    options = data.pop("options", [])
    for field, value in data.items():
        setattr(q, field, value)
    q.options = options
    db.commit()
    db.refresh(q)
    return _question_out(q)


@router.delete("/exams/{exam_id}/questions/{q_id}", status_code=204)
def delete_question(exam_id: int, q_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == q_id, Question.exam_id == exam_id).first()
    if not q:
        raise HTTPException(404, "题目不存在")
    db.delete(q)
    db.commit()


# ===== 答卷查询 =====
@router.get("/exams/{exam_id}/submissions", response_model=list[SubmissionOut])
def list_submissions(exam_id: int, db: Session = Depends(get_db)):
    return db.query(Submission).filter(Submission.exam_id == exam_id).all()


@router.get("/submissions/{sub_id}", response_model=SubmissionOut)
def get_submission(sub_id: int, db: Session = Depends(get_db)):
    sub = db.get(Submission, sub_id)
    if not sub:
        raise HTTPException(404, "答卷不存在")
    return sub


# ===== 辅助：将 ORM 转 schema（处理 options 属性） =====
def _question_out(q: Question) -> QuestionOut:
    return QuestionOut(
        id=q.id,
        exam_id=q.exam_id,
        type=q.type,
        content=q.content,
        score=q.score,
        options=q.options,
        answer=q.answer,
        max_length=q.max_length,
        order_index=q.order_index,
    )
