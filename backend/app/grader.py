"""自动判分逻辑（单选、多选、判断）"""


def grade_answer(q_type: str, std_answer: str, student_answer: str, score: float) -> tuple[bool | None, float]:
    """返回 (is_correct, score_got)；主观题返回 (None, 0)"""
    if q_type == "subjective":
        return None, 0.0

    std = std_answer.strip().upper()
    stu = student_answer.strip().upper()

    if q_type == "single":
        correct = std == stu
        return correct, score if correct else 0.0

    if q_type == "judge":
        # 接受 true/false 或 TRUE/FALSE
        correct = std.lower() == stu.lower()
        return correct, score if correct else 0.0

    if q_type == "multiple":
        # 多选题：完全一致才得分
        std_set = set(std.split(",")) if std else set()
        stu_set = set(stu.split(",")) if stu else set()
        correct = std_set == stu_set and len(stu_set) > 0
        return correct, score if correct else 0.0

    return None, 0.0
