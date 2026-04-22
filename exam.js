/* ===== API 配置 ===== */
const API_BASE = "https://你的项目名.railway.app"; // 替换为 Railway 分配的域名

const API = {
  getExam: () => fetchExamData(),
  submitExam: (payload) => submitExamData(payload),
};

/* ===== API 调用 ===== */
async function fetchExamData() {
  const res = await fetch(`${API_BASE}/api/exam/current`);
  if (!res.ok) throw new Error(`加载失败 (${res.status})`);
  const data = await res.json();
  // 后端字段名转换：order_index → 前端排序，max_length → maxLength
  data.questions = (data.questions || [])
    .sort((a, b) => a.order_index - b.order_index)
    .map((q) => ({ ...q, maxLength: q.max_length }));
  return data;
}

async function submitExamData(payload) {
  // 后端期望 questionId 为数字类型
  const body = {
    ...payload,
    answers: payload.answers.map((a) => ({
      ...a,
      questionId: Number(a.questionId),
    })),
  };
  const res = await fetch(`${API_BASE}/api/exam/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`提交失败 (${res.status})`);
  return res.json();
}

/* ===== 状态 ===== */
const state = {
  exam: null,
  answers: {},      // { qId: value }  single/judge: string, multiple: Set, subjective: string
  studentName: "",
  studentId: "",
  startTime: null,
  timerInterval: null,
  remainingSeconds: 0,
};

/* ===== DOM 引用 ===== */
const $ = (id) => document.getElementById(id);

const screens = {
  loading: $("loading"),
  info: $("info-screen"),
  exam: $("exam-screen"),
  result: $("result-screen"),
};

/* ===== 工具函数 ===== */
function showScreen(name) {
  Object.values(screens).forEach((s) => s.classList.add("hidden"));
  screens[name].classList.remove("hidden");
}

function typeLabel(type) {
  return { single: "单选题", multiple: "多选题", judge: "判断题", subjective: "主观题" }[type] || type;
}

function typeBadgeClass(type) {
  return { single: "badge-single", multiple: "badge-multiple", judge: "badge-judge", subjective: "badge-subjective" }[type] || "";
}

function isAnswered(q) {
  const ans = state.answers[q.id];
  if (q.type === "multiple") return ans instanceof Set && ans.size > 0;
  if (q.type === "subjective") return typeof ans === "string" && ans.trim().length > 0;
  return ans !== undefined && ans !== null && ans !== "";
}

function answeredCount() {
  return state.exam.questions.filter(isAnswered).length;
}

function updateProgress() {
  const total = state.exam.questions.length;
  const done = answeredCount();
  $("answered-count").textContent = done;
  $("total-count").textContent = total;
}

/* ===== 答题卡导航 ===== */
function buildNavGrid() {
  const grid = $("nav-grid");
  grid.innerHTML = "";
  state.exam.questions.forEach((q, i) => {
    const btn = document.createElement("button");
    btn.className = "nav-btn";
    btn.textContent = i + 1;
    btn.title = `第 ${i + 1} 题 · ${typeLabel(q.type)}`;
    btn.addEventListener("click", () => scrollToQuestion(i));
    grid.appendChild(btn);
  });
}

function updateNavGrid() {
  const btns = $("nav-grid").querySelectorAll(".nav-btn");
  state.exam.questions.forEach((q, i) => {
    btns[i].className = "nav-btn" + (isAnswered(q) ? " answered" : "");
  });
  highlightCurrentNav();
}

function highlightCurrentNav() {
  const btns = $("nav-grid").querySelectorAll(".nav-btn");
  const panel = $("question-panel");
  const cards = panel.querySelectorAll(".question-card");
  let currentIdx = 0;
  cards.forEach((card, i) => {
    const rect = card.getBoundingClientRect();
    if (rect.top <= 120) currentIdx = i;
  });
  btns.forEach((b, i) => {
    if (i === currentIdx) b.classList.add("current");
    else b.classList.remove("current");
  });
}

function scrollToQuestion(idx) {
  const cards = $("question-panel").querySelectorAll(".question-card");
  if (cards[idx]) cards[idx].scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ===== 渲染题目 ===== */
function renderQuestions() {
  const panel = $("question-panel");
  panel.innerHTML = "";

  state.exam.questions.forEach((q, i) => {
    const card = document.createElement("div");
    card.className = "question-card";
    card.id = `qcard-${q.id}`;

    card.innerHTML = `
      <div class="question-meta">
        <span class="q-index">第 ${i + 1} 题</span>
        <span class="q-type-badge ${typeBadgeClass(q.type)}">${typeLabel(q.type)}</span>
        <span class="q-score">${q.score} 分</span>
      </div>
      <div class="question-text">${escapeHtml(q.content)}</div>
      <div class="question-input" id="qinput-${q.id}"></div>
    `;

    panel.appendChild(card);
    renderInput(q);
  });

  // 滚动时更新导航高亮
  panel.addEventListener("scroll", highlightCurrentNav, { passive: true });
}

function renderInput(q) {
  const container = $(`qinput-${q.id}`);

  if (q.type === "single") {
    container.innerHTML = `<div class="options-list">${q.options.map((opt) => `
      <label class="option-item" data-key="${opt.key}">
        <input type="radio" name="q_${q.id}" value="${opt.key}" />
        <span class="option-label"><span class="option-key">${opt.key}.</span>${escapeHtml(opt.text)}</span>
      </label>`).join("")}</div>`;

    container.querySelectorAll("input[type=radio]").forEach((radio) => {
      radio.addEventListener("change", () => {
        state.answers[q.id] = radio.value;
        updateOptionHighlight(container, "radio");
        onAnswerChange();
      });
    });

    // 恢复已有答案
    if (state.answers[q.id]) {
      const r = container.querySelector(`input[value="${state.answers[q.id]}"]`);
      if (r) { r.checked = true; updateOptionHighlight(container, "radio"); }
    }
  }

  else if (q.type === "multiple") {
    if (!state.answers[q.id]) state.answers[q.id] = new Set();
    container.innerHTML = `
      <p class="multi-hint">可多选，请选择所有正确选项</p>
      <div class="options-list">${q.options.map((opt) => `
        <label class="option-item" data-key="${opt.key}">
          <input type="checkbox" name="q_${q.id}" value="${opt.key}" />
          <span class="option-label"><span class="option-key">${opt.key}.</span>${escapeHtml(opt.text)}</span>
        </label>`).join("")}</div>`;

    container.querySelectorAll("input[type=checkbox]").forEach((cb) => {
      cb.addEventListener("change", () => {
        const set = state.answers[q.id];
        cb.checked ? set.add(cb.value) : set.delete(cb.value);
        updateOptionHighlight(container, "checkbox");
        onAnswerChange();
      });
      // 恢复
      if (state.answers[q.id].has(cb.value)) { cb.checked = true; }
    });
    updateOptionHighlight(container, "checkbox");
  }

  else if (q.type === "judge") {
    const cur = state.answers[q.id];
    container.innerHTML = `
      <div class="judge-options">
        <button class="judge-btn ${cur === "true" ? "selected-true" : ""}" data-val="true">✓ 正确</button>
        <button class="judge-btn ${cur === "false" ? "selected-false" : ""}" data-val="false">✗ 错误</button>
      </div>`;

    container.querySelectorAll(".judge-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.answers[q.id] = btn.dataset.val;
        container.querySelectorAll(".judge-btn").forEach((b) => {
          b.className = "judge-btn";
          if (b.dataset.val === btn.dataset.val) {
            b.classList.add(btn.dataset.val === "true" ? "selected-true" : "selected-false");
          }
        });
        onAnswerChange();
      });
    });
  }

  else if (q.type === "subjective") {
    const maxLen = q.maxLength || 1000;
    const cur = state.answers[q.id] || "";
    container.innerHTML = `
      <textarea class="subjective-area" maxlength="${maxLen}" placeholder="请在此输入您的答案…">${escapeHtml(cur)}</textarea>
      <div class="char-count"><span class="cur-len">${cur.length}</span> / ${maxLen} 字</div>`;

    const ta = container.querySelector("textarea");
    ta.addEventListener("input", () => {
      state.answers[q.id] = ta.value;
      container.querySelector(".cur-len").textContent = ta.value.length;
      onAnswerChange();
    });
  }
}

function updateOptionHighlight(container, inputType) {
  container.querySelectorAll(".option-item").forEach((label) => {
    const input = label.querySelector(`input[type=${inputType}]`);
    label.classList.toggle("selected", input.checked);
  });
}

function onAnswerChange() {
  updateNavGrid();
  updateProgress();
  // 清除红色高亮（用户已作答）
  state.exam.questions.forEach((q) => {
    if (isAnswered(q)) {
      const card = $(`qcard-${q.id}`);
      if (card) card.classList.remove("unanswered-highlight");
    }
  });
}

/* ===== 计时器 ===== */
function startTimer() {
  if (!state.exam.duration) return; // 0 = 不限时
  state.remainingSeconds = state.exam.duration;
  renderTimer();
  state.timerInterval = setInterval(() => {
    state.remainingSeconds--;
    renderTimer();
    if (state.remainingSeconds <= 0) {
      clearInterval(state.timerInterval);
      autoSubmit();
    }
  }, 1000);
}

function renderTimer() {
  const el = $("timer");
  if (!state.exam.duration) { el.textContent = ""; return; }
  const m = Math.floor(state.remainingSeconds / 60).toString().padStart(2, "0");
  const s = (state.remainingSeconds % 60).toString().padStart(2, "0");
  el.textContent = `${m}:${s}`;
  el.className = "timer";
  if (state.remainingSeconds <= 300) el.classList.add("warning");
  if (state.remainingSeconds <= 60) el.classList.add("danger");
}

function autoSubmit() {
  clearInterval(state.timerInterval);
  doSubmit();
}

/* ===== 提交逻辑 ===== */
$("submit-btn").addEventListener("click", () => {
  const unanswered = state.exam.questions.filter((q) => !isAnswered(q));

  if (unanswered.length > 0) {
    // 高亮未答题目
    unanswered.forEach((q) => {
      const card = $(`qcard-${q.id}`);
      if (card) card.classList.add("unanswered-highlight");
    });
    // 滚动到第一道未答题
    const firstIdx = state.exam.questions.indexOf(unanswered[0]);
    scrollToQuestion(firstIdx);

    $("confirm-msg").textContent =
      `您还有 ${unanswered.length} 道题未作答（已用红框标出），确定要提交吗？`;
  } else {
    $("confirm-msg").textContent = "所有题目均已作答，确认提交试卷？";
  }

  $("confirm-modal").classList.remove("hidden");
});

$("confirm-cancel").addEventListener("click", () => {
  $("confirm-modal").classList.add("hidden");
});

$("confirm-ok").addEventListener("click", () => {
  $("confirm-modal").classList.add("hidden");
  doSubmit();
});

// 点击遮罩关闭
$("confirm-modal").addEventListener("click", (e) => {
  if (e.target === $("confirm-modal")) $("confirm-modal").classList.add("hidden");
});

async function doSubmit() {
  clearInterval(state.timerInterval);

  const payload = {
    examId: state.exam.id,
    studentName: state.studentName,
    studentId: state.studentId,
    submitTime: new Date().toISOString(),
    answers: state.exam.questions.map((q) => {
      let value = state.answers[q.id];
      if (q.type === "multiple") value = value instanceof Set ? [...value].sort().join(",") : "";
      return { questionId: q.id, type: q.type, answer: value ?? "" };
    }),
  };

  await API.submitExam(payload);

  const total = state.exam.questions.length;
  const done = answeredCount();
  const elapsed = Math.floor((Date.now() - state.startTime) / 1000);
  const em = Math.floor(elapsed / 60).toString().padStart(2, "0");
  const es = (elapsed % 60).toString().padStart(2, "0");

  $("result-student").textContent = `考生：${state.studentName}${state.studentId ? "  考号：" + state.studentId : ""}`;
  $("result-total").textContent = total;
  $("result-answered").textContent = done;
  $("result-unanswered").textContent = total - done;
  $("result-time").textContent = `用时 ${em}:${es}`;
  document.querySelector(".stat:first-child .stat-label").textContent = `共 ${total} 题`;

  showScreen("result");
}

/* ===== 开始考试 ===== */
$("start-btn").addEventListener("click", () => {
  const nameInput = $("student-name");
  const name = nameInput.value.trim();

  if (!name) {
    nameInput.classList.add("error");
    $("name-error").classList.remove("hidden");
    nameInput.focus();
    return;
  }

  nameInput.classList.remove("error");
  $("name-error").classList.add("hidden");

  state.studentName = name;
  state.studentId = $("student-id").value.trim();
  state.startTime = Date.now();

  $("header-exam-name").textContent = state.exam.title;
  $("header-student-name").textContent = state.studentName;

  showScreen("exam");
  buildNavGrid();
  renderQuestions();
  updateNavGrid();
  updateProgress();
  startTimer();
});

$("student-name").addEventListener("input", () => {
  if ($("student-name").value.trim()) {
    $("student-name").classList.remove("error");
    $("name-error").classList.add("hidden");
  }
});

/* ===== 初始化 ===== */
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

(async function init() {
  showScreen("loading");
  try {
    state.exam = await API.getExam();
    $("exam-title").textContent = state.exam.title;
    $("exam-desc").textContent = state.exam.description || "";
    showScreen("info");
  } catch (err) {
    screens.loading.innerHTML = `<p style="color:var(--danger);padding:40px">加载失败，请刷新重试。<br><small>${err.message}</small></p>`;
  }
})();
