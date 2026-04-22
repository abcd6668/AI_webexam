"""考生端接口：获取试卷、提交答案"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Exam, Question, Submission, Answer
from ..schemas import ExamPublic, QuestionOutNoAnswer, SubmitRequest, SubmissionOut
from ..grader import grade_answer

router = APIRouter(prefix="/api/exam", tags=["考生端"])


@router.get("/current", response_model=ExamPublic)
def get_active_exam(db: Session = Depends(get_db)):
    """获取当前启用的最新试卷（考生端调用）"""
    exam = (
        db.query(Exam)
        .filter(Exam.is_active == True)
        .order_by(Exam.created_at.desc())
        .first()
    )
    if not exam:
        raise HTTPException(404, "暂无可用试卷")
    return _to_public(exam)


@router.get("/{exam_id}", response_model=ExamPublic)
def get_exam_by_id(exam_id: int, db: Session = Depends(get_db)):
    """按 ID 获取试卷（不含答案）"""
    exam = db.get(Exam, exam_id)
    if not exam or not exam.is_active:
        raise HTTPException(404, "试卷不存在或已停用")
    return _to_public(exam)


@router.post("/submit", response_model=SubmissionOut, status_code=201)
def submit_exam(body: SubmitRequest, db: Session = Depends(get_db)):
    exam = db.get(Exam, body.examId)
    if not exam:
        raise HTTPException(404, "试卷不存在")

    # 建立题目索引
    questions: dict[int, Question] = {q.id: q for q in exam.questions}

    submission = Submission(
        exam_id=exam.id,
        student_name=body.studentName,
        student_id=body.studentId,
    )
    db.add(submission)
    db.flush()  # 获取 submission.id

    auto_score = 0.0
    total_auto_score = 0.0

    for ans_in in body.answers:
        q = questions.get(ans_in.questionId)
        if not q:
            continue

        is_correct, score_got = grade_answer(q.type, q.answer, ans_in.answer, q.score)

        if q.type != "subjective":
            total_auto_score += q.score
            auto_score += score_got

        answer = Answer(
            submission_id=submission.id,
            question_id=q.id,
            answer=ans_in.answer,
            is_correct=is_correct,
            score_got=score_got,
        )
        db.add(answer)

    submission.auto_score = auto_score
    submission.total_auto_score = total_auto_score

    db.commit()
    db.refresh(submission)
    return submission


# ===== 辅助 =====
def _to_public(exam: Exam) -> ExamPublic:
    return ExamPublic(
        id=exam.id,
        title=exam.title,
        description=exam.description,
        duration=exam.duration,
        questions=[
            QuestionOutNoAnswer(
                id=q.id,
                exam_id=q.exam_id,
                type=q.type,
                content=q.content,
                score=q.score,
                options=q.options,
                max_length=q.max_length,
                order_index=q.order_index,
            )
            for q in exam.questions
        ],
    )
