# Feature Pack "Hòa Tiến số" Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thêm 11 tính năng "ăn điểm" cho web dự thi: log toàn bộ chat + feedback 👍👎 + thống kê, voice input, in checklist hồ sơ, chips động, social proof, share, PWA + favicon, sửa history replay, a11y modal.

**Architecture:** Backend FastAPI thêm 3 việc nhỏ (log mọi lượt chat kể cả khách vãng lai/unmatched, cột feedback + endpoint, 2 endpoint stats public/admin). Frontend static thêm UI thuần JS/CSS, không framework. Response schema `/chat` chỉ **thêm field** (`message_id`, `matched_source_id`) — không đổi field cũ.

**Tech Stack:** FastAPI + SQLAlchemy + Alembic (backend), vanilla JS/CSS (frontend), Web Speech API, Web Share API, Service Worker.

## Global Constraints

- **Không có test suite trong repo** — kiểm thử bằng curl + trình duyệt theo checklist thủ công (quy ước repo, xem CLAUDE.md). Mỗi task có bước verify cụ thể.
- Schema DB đổi → **luôn qua Alembic migration**, không sửa tay (rules/data-schema.md).
- Màu sắc frontend **chỉ dùng CSS variables** đã có (`--paddy`, `--river`, `--rice`, `--cream`, `--ink`, `--line`…), không hardcode hex mới (rules/frontend.md).
- Response lỗi backend dạng `{"detail": "..."}` đúng HTTP status (rules/backend.md).
- Không thêm dependency Python/JS mới.
- Không chặn trải nghiệm bằng đăng nhập: feedback 👍👎 và chat dùng được ẩn danh.
- Backend dev local: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000`. Frontend: `cd frontend && python3 -m http.server 5500`.
- Commit sau mỗi task, message tiếng Anh `feat:`/`fix:` như lịch sử git.

---

### Task 1: Backend — log mọi lượt chat, trả `message_id` + `matched_source_id`

Hiện tại `/chat` chỉ lưu `chat_history` khi user đăng nhập → không có dữ liệu thống kê câu unmatched/khách vãng lai. Cột `user_id` đã nullable sẵn (migration không cần). Frontend cần `message_id` để gửi feedback và `matched_source_id` (code thủ tục) để build checklist in.

**Files:**
- Modify: `backend/app/schemas/chat.py`
- Modify: `backend/app/routers/chat.py:30-48`

**Interfaces:**
- Produces: `ChatResponse` thêm `message_id: uuid.UUID | None` và `matched_source_id: str | None`. Task 2 dùng `message_id`; Task 7 dùng `matched_source_id`.

- [ ] **Step 1: Thêm field vào `ChatResponse`** (`backend/app/schemas/chat.py`)

```python
class ChatResponse(BaseModel):
    answer_html: str
    source: str
    matched: bool
    matched_source_type: str
    # Chỉ có khi matched thủ tục — frontend dùng để sinh QR nộp hồ sơ trực tuyến
    online_url: str | None = None
    # Frontend dùng message_id để gửi feedback 👍👎, matched_source_id (code thủ tục) để in checklist
    message_id: uuid.UUID | None = None
    matched_source_id: str | None = None
```

- [ ] **Step 2: Sửa `routers/chat.py` — luôn lưu ChatHistory (user_id=None nếu ẩn danh), trả field mới**

Thay đoạn `if current_user is not None: ...` và `return ChatResponse(...)` bằng:

```python
    # Lưu mọi lượt chat (kể cả khách vãng lai, user_id=None) để thống kê câu hỏi
    # phổ biến & câu chưa trả lời được. /chat/history vẫn lọc theo user_id nên
    # khách ẩn danh không thấy gì thay đổi.
    entry = ChatHistory(
        user_id=current_user.id if current_user else None,
        question=payload.question,
        answer=result["answer_html"],
        matched_source_type=result["matched_source_type"],
        matched_source_id=result.get("matched_source_id"),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return ChatResponse(
        answer_html=result["answer_html"],
        source=result["source"],
        matched=result["matched"],
        matched_source_type=result["matched_source_type"],
        online_url=result.get("online_url"),
        message_id=entry.id,
        matched_source_id=result.get("matched_source_id"),
    )
```

- [ ] **Step 3: Verify bằng curl**

```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --port 8000 &
curl -s -X POST localhost:8000/chat -H 'Content-Type: application/json' -d '{"question":"làm khai sinh cần gì"}'
```
Expected: JSON có `message_id` (uuid) và `matched_source_id` (vd `KS-01`). Gửi thêm 1 câu vô nghĩa (`"question":"asdjkasd"`) → vẫn có `message_id`, `matched_source_type: "none"`. Kiểm tra DB: `SELECT count(*) FROM chat_history WHERE user_id IS NULL;` tăng 2.

- [ ] **Step 4: Commit**

```bash
git add backend/app/schemas/chat.py backend/app/routers/chat.py
git commit -m "feat: log all chat turns (incl. anonymous/unmatched), return message_id"
```

---

### Task 2: Backend — cột `feedback_helpful` + endpoint `POST /chat/feedback`

**Files:**
- Modify: `backend/app/models/chat_history.py`
- Modify: `backend/app/schemas/chat.py`
- Modify: `backend/app/routers/chat.py`
- Create: `backend/alembic/versions/<autogen>_add_feedback_helpful.py` (autogenerate)

**Interfaces:**
- Consumes: `message_id` từ Task 1.
- Produces: `POST /chat/feedback` body `{"message_id": "<uuid>", "helpful": true|false}` → 204. Task 5 (frontend) gọi qua `api.sendFeedback(messageId, helpful)`; Task 3 aggregate cột này.

- [ ] **Step 1: Thêm cột vào model** (`backend/app/models/chat_history.py`, sau `matched_source_id`)

```python
    # 👍👎 của người dùng trên câu trả lời — null = chưa đánh giá
    feedback_helpful: Mapped[bool | None] = mapped_column(nullable=True)
```

- [ ] **Step 2: Tạo migration autogenerate + kiểm tra nội dung**

```bash
cd backend && alembic revision --autogenerate -m "add feedback_helpful to chat_history"
```
Mở file sinh ra, xác nhận chỉ có `op.add_column('chat_history', sa.Column('feedback_helpful', sa.Boolean(), nullable=True))` và downgrade tương ứng — xoá mọi diff thừa nếu autogen nhặt nhầm.

- [ ] **Step 3: Chạy migration**

```bash
alembic upgrade head
```
Expected: `Running upgrade ... add feedback_helpful`.

- [ ] **Step 4: Thêm schema + endpoint**

`backend/app/schemas/chat.py`:

```python
class FeedbackRequest(BaseModel):
    message_id: uuid.UUID
    helpful: bool
```

`backend/app/routers/chat.py` (import thêm `HTTPException`, `FeedbackRequest`; đặt sau handler `chat`):

```python
@router.post("/feedback", status_code=204)
@limiter.limit(settings.rate_limit_chat)
def chat_feedback(request: Request, payload: FeedbackRequest, db: Session = Depends(get_db)):
    """Ghi nhận 👍👎 — không cần đăng nhập, message_id là UUID không đoán được."""
    entry = db.get(ChatHistory, payload.message_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu trả lời")
    entry.feedback_helpful = payload.helpful
    db.commit()
```

- [ ] **Step 5: Verify bằng curl**

```bash
MSG=$(curl -s -X POST localhost:8000/chat -H 'Content-Type: application/json' -d '{"question":"giờ làm việc"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["message_id"])')
curl -s -o /dev/null -w '%{http_code}' -X POST localhost:8000/chat/feedback -H 'Content-Type: application/json' -d "{\"message_id\":\"$MSG\",\"helpful\":true}"
```
Expected: `204`. UUID bịa → `404`.

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/chat_history.py backend/app/schemas/chat.py backend/app/routers/chat.py backend/alembic/versions/
git commit -m "feat: answer feedback (thumbs up/down) endpoint + column"
```

---

### Task 3: Backend — stats: `GET /chat/stats/public` + `GET /admin/stats`

**Files:**
- Modify: `backend/app/schemas/chat.py`
- Modify: `backend/app/routers/chat.py`
- Modify: `backend/app/routers/admin.py`

**Interfaces:**
- Produces:
  - `GET /chat/stats/public` (public) → `{"total_answered": int, "top_questions": ["Đăng ký khai sinh", ...]}` — `total_answered` = số lượt matched; `top_questions` = tối đa 4 tên thủ tục được hỏi nhiều nhất. Task 8 dùng cho chips động + hero.
  - `GET /admin/stats` (admin) → `{"total": int, "matched": int, "unmatched": int, "helpful": int, "unhelpful": int, "top_procedures": [{"name": str, "count": int}], "recent_unmatched": [{"question": str, "created_at": iso}]}`. Task 13 dùng.

- [ ] **Step 1: Thêm schemas** (`backend/app/schemas/chat.py`)

```python
class PublicStatsOut(BaseModel):
    total_answered: int
    top_questions: list[str]


class TopProcedureOut(BaseModel):
    name: str
    count: int


class UnmatchedQuestionOut(BaseModel):
    question: str
    created_at: datetime


class AdminStatsOut(BaseModel):
    total: int
    matched: int
    unmatched: int
    helpful: int
    unhelpful: int
    top_procedures: list[TopProcedureOut]
    recent_unmatched: list[UnmatchedQuestionOut]
```

- [ ] **Step 2: Endpoint public** (`backend/app/routers/chat.py` — import `func` từ `sqlalchemy`, `Procedure` từ `app.models`, schemas mới)

```python
def _top_procedures(db: Session, limit: int) -> list[tuple[str, int]]:
    """[(tên thủ tục, số lượt hỏi)] xếp giảm dần, join qua code trong matched_source_id."""
    rows = (
        db.query(ChatHistory.matched_source_id, func.count().label("n"))
        .filter(ChatHistory.matched_source_type == "procedure", ChatHistory.matched_source_id.isnot(None))
        .group_by(ChatHistory.matched_source_id)
        .order_by(func.count().desc())
        .limit(limit)
        .all()
    )
    names = {p.code: p.name for p in db.query(Procedure).filter(Procedure.code.in_([r[0] for r in rows]))}
    return [(names[code], n) for code, n in rows if code in names]


@router.get("/stats/public", response_model=PublicStatsOut)
def public_stats(db: Session = Depends(get_db)):
    total = db.query(ChatHistory).filter(ChatHistory.matched_source_type != "none").count()
    return PublicStatsOut(total_answered=total, top_questions=[name for name, _ in _top_procedures(db, 4)])
```

**Lưu ý thứ tự route:** đặt `public_stats` TRƯỚC `get_history` trong file là đủ; path `/chat/stats/public` không xung đột `/chat/history`.

- [ ] **Step 3: Endpoint admin** (`backend/app/routers/admin.py` — import `func`, `ChatHistory`, schemas, và `_top_procedures` từ `app.routers.chat`)

```python
from app.models import ChatHistory
from app.routers.chat import _top_procedures
from app.schemas.chat import AdminStatsOut, TopProcedureOut, UnmatchedQuestionOut


@router.get("/stats", response_model=AdminStatsOut)
def admin_stats(db: Session = Depends(get_db)):
    total = db.query(ChatHistory).count()
    unmatched = db.query(ChatHistory).filter(ChatHistory.matched_source_type == "none").count()
    helpful = db.query(ChatHistory).filter(ChatHistory.feedback_helpful.is_(True)).count()
    unhelpful = db.query(ChatHistory).filter(ChatHistory.feedback_helpful.is_(False)).count()
    recent = (
        db.query(ChatHistory)
        .filter(ChatHistory.matched_source_type == "none")
        .order_by(ChatHistory.created_at.desc())
        .limit(20)
        .all()
    )
    return AdminStatsOut(
        total=total,
        matched=total - unmatched,
        unmatched=unmatched,
        helpful=helpful,
        unhelpful=unhelpful,
        top_procedures=[TopProcedureOut(name=n, count=c) for n, c in _top_procedures(db, 10)],
        recent_unmatched=[UnmatchedQuestionOut(question=r.question, created_at=r.created_at) for r in recent],
    )
```

- [ ] **Step 4: Verify bằng curl**

```bash
curl -s localhost:8000/chat/stats/public
# Expected: {"total_answered": >=1, "top_questions": [...]} sau các câu test ở Task 1-2
curl -s -o /dev/null -w '%{http_code}' localhost:8000/admin/stats
# Expected: 401 (chưa đăng nhập)
TOKEN=$(curl -s -X POST localhost:8000/auth/login -H 'Content-Type: application/json' -d '{"email":"<admin email>","password":"<admin pass>"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
curl -s localhost:8000/admin/stats -H "Authorization: Bearer $TOKEN"
# Expected: JSON đầy đủ các field
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/chat.py backend/app/routers/chat.py backend/app/routers/admin.py
git commit -m "feat: public + admin chat statistics endpoints"
```

---

### Task 4: Frontend — mở rộng `api.js`

**Files:**
- Modify: `frontend/js/api.js:50-61`

**Interfaces:**
- Produces: `api.sendFeedback(messageId, helpful)`, `api.getPublicStats()`, `api.getAdminStats()` — Task 5, 8, 13 dùng.

- [ ] **Step 1: Thêm 3 hàm vào object `api`**

```js
  sendFeedback: (messageId, helpful) =>
    apiFetch("/chat/feedback", { method: "POST", body: JSON.stringify({ message_id: messageId, helpful }) }),
  getPublicStats: () => apiFetch("/chat/stats/public"),
  getAdminStats: () => apiFetch("/admin/stats"),
```

- [ ] **Step 2: Verify** — mở `http://localhost:5500`, console: `await api.getPublicStats()` trả object. 

- [ ] **Step 3: Commit**

```bash
git add frontend/js/api.js
git commit -m "feat: api client for feedback + stats"
```

---

### Task 5: Frontend — 👍👎 dưới câu trả lời bot

**Files:**
- Modify: `frontend/js/app.js` (hàm `ask`, thêm hàm `addFeedbackBar`)
- Modify: `frontend/css/style.css`

**Interfaces:**
- Consumes: `api.sendFeedback` (Task 4), `res.message_id` (Task 1).

- [ ] **Step 1: Thêm hàm `addFeedbackBar` vào app.js** (sau `buildAnswerHtml`)

```js
function addFeedbackBar(msgEl, messageId) {
  if (!messageId) return;
  const bar = document.createElement('div');
  bar.className = 'fb-bar';
  bar.innerHTML = `<span>Câu trả lời có hữu ích?</span>
    <button class="fb-btn" data-v="1" aria-label="Hữu ích">👍</button>
    <button class="fb-btn" data-v="0" aria-label="Chưa hữu ích">👎</button>`;
  bar.querySelectorAll('.fb-btn').forEach(btn => {
    btn.onclick = async () => {
      try { await api.sendFeedback(messageId, btn.dataset.v === '1'); } catch (_) {}
      bar.innerHTML = `<span class="fb-done">Cảm ơn bạn đã góp ý! 🙏</span>`;
    };
  });
  msgEl.querySelector('.bubble').appendChild(bar);
}
```

- [ ] **Step 2: Gọi trong `ask()`** — thay dòng `addMsg('bot', buildAnswerHtml(res), res.source);` bằng:

```js
    const botMsg = addMsg('bot', buildAnswerHtml(res), res.source);
    addFeedbackBar(botMsg, res.message_id);
```

- [ ] **Step 3: CSS** (thêm cuối phần Chat trong style.css)

```css
  .fb-bar { margin-top:9px; padding-top:9px; border-top:1px dashed var(--line); display:flex; align-items:center; gap:8px; font-size:12px; color:var(--ink-soft); }
  .fb-btn { background:var(--white); border:1px solid var(--line); border-radius:8px; padding:3px 9px; cursor:pointer; font-size:13px; transition:.2s; }
  .fb-btn:hover { border-color:var(--paddy); transform:scale(1.08); }
  .fb-done { color:var(--paddy-deep); font-weight:600; }
```

- [ ] **Step 4: Verify** — hỏi 1 câu trong trình duyệt → thấy 👍👎, bấm 👍 → "Cảm ơn bạn đã góp ý!", Network tab thấy `POST /chat/feedback` 204.

- [ ] **Step 5: Commit**

```bash
git add frontend/js/app.js frontend/css/style.css
git commit -m "feat: thumbs up/down feedback on bot answers"
```

---

### Task 6: Frontend — hỏi bằng giọng nói (Web Speech API)

**Files:**
- Modify: `frontend/index.html:95-100` (thêm nút mic trong `.chat-input`)
- Modify: `frontend/js/app.js`
- Modify: `frontend/css/style.css`

- [ ] **Step 1: Thêm nút mic vào index.html** (trong `.chat-input`, TRƯỚC nút send)

```html
        <button class="mic-btn" id="micBtn" aria-label="Hỏi bằng giọng nói" title="Hỏi bằng giọng nói">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" stroke="currentColor" stroke-width="2"/><path d="M19 10v1a7 7 0 0 1-14 0v-1M12 18v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        </button>
```

- [ ] **Step 2: Logic voice trong app.js** (thêm section mới sau phần Chat UI; init trong `DOMContentLoaded`)

```js
/* ---------- Voice input (Web Speech API) ---------- */
function initVoiceInput() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const micBtn = document.getElementById('micBtn');
  if (!SR) { micBtn.style.display = 'none'; return; }

  const rec = new SR();
  rec.lang = 'vi-VN';
  rec.interimResults = true;
  let listening = false;

  rec.onresult = (e) => {
    const transcript = Array.from(e.results).map(r => r[0].transcript).join('');
    document.getElementById('chatInput').value = transcript;
    if (e.results[e.results.length - 1].isFinal) ask(transcript);
  };
  rec.onend = () => { listening = false; micBtn.classList.remove('listening'); };
  rec.onerror = () => { listening = false; micBtn.classList.remove('listening'); };

  micBtn.onclick = () => {
    if (listening) { rec.stop(); return; }
    listening = true;
    micBtn.classList.add('listening');
    rec.start();
  };
}
```

Trong `DOMContentLoaded` (sau `updateAuthUI();`): `initVoiceInput();`

- [ ] **Step 3: CSS**

```css
  .mic-btn { background:var(--white); color:var(--river-deep); border:1px solid var(--line); border-radius:12px; width:48px; cursor:pointer; display:grid; place-items:center; transition:.2s; flex-shrink:0; }
  .mic-btn:hover { border-color:var(--paddy); color:var(--paddy-deep); }
  .mic-btn.listening { background:var(--paddy); color:#fff; border-color:var(--paddy); animation:pulse 1.5s infinite; }
```

- [ ] **Step 4: Verify** — Chrome localhost: bấm mic → browser xin quyền micro → nói "giờ làm việc của xã" → text hiện dần trong input, tự gửi khi nói xong. (Safari không có webkitSpeechRecognition đầy đủ → nút tự ẩn, kiểm tra bằng cách set `window.SpeechRecognition=undefined;window.webkitSpeechRecognition=undefined` trước init.)

- [ ] **Step 5: Commit**

```bash
git add frontend/index.html frontend/js/app.js frontend/css/style.css
git commit -m "feat: voice input via Web Speech API (vi-VN)"
```

---

### Task 7: Frontend — nút "In checklist hồ sơ" + print CSS

**Files:**
- Modify: `frontend/index.html` (thêm `<div id="printArea"></div>` trước `</body>`)
- Modify: `frontend/js/app.js` (hàm `printChecklist`, nút trong chat + modal)
- Modify: `frontend/css/style.css` (print CSS)

**Interfaces:**
- Consumes: `res.matched_source_id` (Task 1) — code thủ tục, tra trong mảng `PROCEDURES` toàn cục (đã load sẵn, mỗi phần tử có `code, name, documents, fee, processing_time, place_of_submission, online_url`).

- [ ] **Step 1: index.html** — trước `</body>`:

```html
<div id="printArea" aria-hidden="true"></div>
```

- [ ] **Step 2: app.js — hàm build + print** (sau `buildAnswerHtml`)

```js
function printChecklist(code) {
  const p = PROCEDURES.find(x => x.code === code);
  if (!p) return;
  document.getElementById('printArea').innerHTML = `
    <h1>UBND xã Hòa Tiến — Checklist hồ sơ</h1>
    <h2>${p.name}</h2>
    <p>${p.description}</p>
    <h3>Hồ sơ cần chuẩn bị (đánh dấu khi đã có):</h3>
    <ul>${p.documents.map(d => `<li>☐ ${d}</li>`).join('')}</ul>
    <p><b>Lệ phí:</b> ${p.fee} — <b>Thời gian xử lý:</b> ${p.processing_time}</p>
    <p><b>Nơi nộp:</b> ${p.place_of_submission}</p>
    <p><b>Nộp trực tuyến:</b> ${p.online_url}</p>
    <p class="print-foot">In từ Trợ lý hành chính số Hòa Tiến AI · ${new Date().toLocaleDateString('vi-VN')} · Thông tin tham khảo, đối soát tại Bộ phận Một cửa.</p>`;
  window.print();
}
```

- [ ] **Step 3: Nút in trong chat** — trong `ask()`, sau `addFeedbackBar(botMsg, res.message_id);`:

```js
    if (res.matched_source_type === 'procedure' && res.matched_source_id) {
      const pr = document.createElement('button');
      pr.className = 'print-btn';
      pr.innerHTML = '🖨️ In checklist hồ sơ';
      pr.onclick = () => printChecklist(res.matched_source_id);
      botMsg.querySelector('.bubble').appendChild(pr);
    }
```

Và trong `openModal(p)` — thêm nút cạnh `.modal-cta` (trước thẻ `<a ...modal-cta>`):

```html
      <button class="btn btn-ghost modal-cta" onclick="printChecklist('${p.code}')">🖨️ In checklist hồ sơ</button>
```

(Lưu ý: `ProcedureOut` phải trả `code` — kiểm tra `backend/app/schemas/procedure.py`, nếu thiếu thì thêm `code: str`.)

- [ ] **Step 4: Print CSS** (cuối style.css)

```css
  /* ── In checklist hồ sơ ── */
  .print-btn { margin-top:9px; display:inline-flex; background:var(--white); border:1px solid var(--line); border-radius:8px; padding:6px 12px; cursor:pointer; font-size:12.5px; font-family:inherit; font-weight:600; color:var(--ink); transition:.2s; }
  .print-btn:hover { border-color:var(--paddy); color:var(--paddy-deep); }
  #printArea { display:none; }
  @media print {
    body > *:not(#printArea) { display:none !important; }
    #printArea { display:block !important; font-family:'Be Vietnam Pro', system-ui, sans-serif; color:#000; padding:24px; }
    #printArea h1 { font-size:15px; text-transform:uppercase; letter-spacing:.5px; }
    #printArea h2 { font-size:22px; margin:10px 0 6px; }
    #printArea h3 { font-size:14px; margin:14px 0 6px; }
    #printArea ul { list-style:none; padding-left:4px; }
    #printArea li { margin:7px 0; font-size:14px; }
    #printArea .print-foot { margin-top:20px; font-size:11px; color:#555; border-top:1px solid #ccc; padding-top:8px; }
  }
```

- [ ] **Step 5: Verify** — hỏi "làm khai sinh" → nút 🖨️ hiện → bấm → hộp thoại in chỉ hiển thị checklist (không lộ trang web phía sau). Mở modal thủ tục → nút in cũng hoạt động. Đóng print preview, trang bình thường trở lại.

- [ ] **Step 6: Commit**

```bash
git add frontend/index.html frontend/js/app.js frontend/css/style.css
git commit -m "feat: printable document checklist for procedures"
```

---

### Task 8: Frontend — sửa history replay (không gọi lại API)

**Files:**
- Modify: `frontend/js/app.js:215-234` (hàm `loadHistory`)

- [ ] **Step 1: Sửa `loadHistory`** — thay handler click. Trong template item thêm `data-a`:

```js
    panel.innerHTML = items.map((h, i) => `
      <div class="history-item" data-i="${i}">
        <div class="hq">${h.question}</div>
        <div class="ht">${new Date(h.created_at).toLocaleString('vi-VN')}</div>
      </div>`).join('');
    panel.querySelectorAll('.history-item').forEach(el => {
      el.onclick = () => {
        // Hiển thị lại câu trả lời đã lưu — không gọi API hỏi lại (nhanh, không tốn quota, không đổi nội dung)
        const h = items[Number(el.dataset.i)];
        addMsg('user', h.question);
        addMsg('bot', h.answer, 'Từ lịch sử đã lưu · ' + new Date(h.created_at).toLocaleDateString('vi-VN'));
        panel.classList.remove('show');
      };
    });
```

Đồng thời trong `ask()` bỏ dòng `if (getToken()) loadHistory();` → thay bằng: chỉ reload nếu panel đang mở:

```js
    if (getToken() && document.getElementById('historyPanel').classList.contains('show')) loadHistory();
```

- [ ] **Step 2: Verify** — đăng nhập, hỏi 1 câu, mở Lịch sử, click item → câu Q/A cũ hiện ngay lập tức (không có typing indicator, không có request `/chat` trong Network tab).

- [ ] **Step 3: Commit**

```bash
git add frontend/js/app.js
git commit -m "fix: history click replays saved answer instead of re-asking API"
```

---

### Task 9: Frontend — chips gợi ý động + social proof trên hero

**Files:**
- Modify: `frontend/index.html:50-54` (hero-stats)
- Modify: `frontend/js/app.js` (DOMContentLoaded)

**Interfaces:**
- Consumes: `api.getPublicStats()` (Task 4) → `{total_answered, top_questions}`.

- [ ] **Step 1: index.html — thêm stat động vào `.hero-stats`** (thay `<div><b>24/7</b><span>Hỗ trợ mọi lúc</span></div>` giữ nguyên, chỉ THÊM 1 div đầu tiên, ẩn mặc định):

```html
      <div id="statAnswered" style="display:none;"><b id="statAnsweredNum">0</b><span>Câu hỏi đã trả lời</span></div>
```

- [ ] **Step 2: app.js — refactor chips + load stats.** Trong `DOMContentLoaded`, thay khối chips cứng bằng:

```js
  const DEFAULT_CHIPS = ['Làm khai sinh cần gì?', 'Đăng ký kết hôn', 'Giờ làm việc?', 'Chứng thực bản sao'];
  function renderChips(list) {
    const chipBox = document.getElementById('quickChips');
    chipBox.innerHTML = '';
    list.forEach(c => {
      const b = document.createElement('button');
      b.className = 'chip-q'; b.textContent = c;
      b.onclick = () => ask(c);
      chipBox.appendChild(b);
    });
  }
  renderChips(DEFAULT_CHIPS);

  // Chips động theo thủ tục được hỏi nhiều + social proof — lỗi thì giữ mặc định
  api.getPublicStats().then(s => {
    if (s.top_questions && s.top_questions.length >= 3) renderChips(s.top_questions);
    if (s.total_answered >= 10) {
      document.getElementById('statAnsweredNum').textContent = s.total_answered.toLocaleString('vi-VN');
      document.getElementById('statAnswered').style.display = '';
    }
  }).catch(() => {});
```

(Ngưỡng `>= 10` để hero không khoe con số 3 lúc mới seed; `>= 3` chips để không hiện 1 chip lẻ loi.)

- [ ] **Step 3: Verify** — trình duyệt: chips mặc định hiện ngay; sau vài chục câu test, reload → chips đổi theo top thủ tục, hero hiện "N Câu hỏi đã trả lời". Tắt backend → chips mặc định vẫn hiện, không lỗi console.

- [ ] **Step 4: Commit**

```bash
git add frontend/index.html frontend/js/app.js
git commit -m "feat: dynamic suggestion chips + hero social proof from public stats"
```

---

### Task 10: Frontend — nút Chia sẻ (Zalo/Web Share)

**Files:**
- Modify: `frontend/index.html:46-49` (hero-actions)
- Modify: `frontend/js/app.js`
- Modify: `frontend/css/style.css`

- [ ] **Step 1: index.html — thêm nút vào `.hero-actions`:**

```html
      <button class="btn btn-ghost" id="shareBtn">Chia sẻ 💬</button>
```

Và popover ngay sau `.hero-actions` (trong `.hero-copy`):

```html
    <div class="share-pop" id="sharePop">
      <img id="shareQr" alt="QR chia sẻ trang" />
      <div>
        <b>Chia sẻ cho bà con</b>
        <small>Quét QR bằng điện thoại, hoặc sao chép liên kết gửi qua Zalo.</small>
        <button class="btn btn-primary" id="copyLinkBtn" style="padding:8px 14px; font-size:13px;">Sao chép liên kết</button>
      </div>
    </div>
```

- [ ] **Step 2: app.js — logic share** (section mới, init trong DOMContentLoaded):

```js
/* ---------- Chia sẻ (Zalo / Web Share) ---------- */
function initShare() {
  const url = location.href.split('#')[0];
  document.getElementById('shareBtn').onclick = async () => {
    if (navigator.share) {
      // Mobile: sheet hệ thống có sẵn Zalo/Messenger
      try { await navigator.share({ title: 'Hòa Tiến AI · Trợ lý hành chính số', url }); } catch (_) {}
      return;
    }
    const pop = document.getElementById('sharePop');
    pop.classList.toggle('show');
    document.getElementById('shareQr').src = qr(url, 110);
  };
  document.getElementById('copyLinkBtn').onclick = async (e) => {
    try { await navigator.clipboard.writeText(url); e.target.textContent = 'Đã sao chép ✓'; } catch (_) {}
  };
}
```

- [ ] **Step 3: CSS**

```css
  /* ── Chia sẻ ── */
  .share-pop { display:none; margin-top:14px; background:var(--white); border:1px solid var(--line); border-radius:12px; padding:14px; box-shadow:var(--shadow); align-items:center; gap:14px; max-width:360px; }
  .share-pop.show { display:flex; }
  .share-pop img { width:96px; height:96px; border-radius:8px; }
  .share-pop b { display:block; font-size:14px; }
  .share-pop small { display:block; color:var(--ink-soft); font-size:12px; margin:4px 0 10px; }
```

- [ ] **Step 4: Verify** — desktop: bấm Chia sẻ → popover QR + "Sao chép liên kết" → clipboard đúng URL. Mobile (hoặc DevTools device mode với `navigator.share` có sẵn): mở share sheet hệ thống.

- [ ] **Step 5: Commit**

```bash
git add frontend/index.html frontend/js/app.js frontend/css/style.css
git commit -m "feat: share button (Web Share API + QR/copy-link fallback)"
```

---

### Task 11: Frontend — favicon + PWA (manifest + service worker)

**Files:**
- Create: `frontend/icons/icon.svg`
- Create: `frontend/manifest.webmanifest`
- Create: `frontend/sw.js`
- Modify: `frontend/index.html` (head + script đăng ký SW)

- [ ] **Step 1: Icon SVG** (`frontend/icons/icon.svg`) — mộc "HT" đúng brand seal (gradient paddy→river):

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#2f7d4f"/><stop offset="1" stop-color="#1d6f8b"/>
  </linearGradient></defs>
  <rect width="100" height="100" rx="24" fill="url(#g)"/>
  <text x="50" y="66" font-family="system-ui,sans-serif" font-size="42" font-weight="800" fill="#fff" text-anchor="middle">HT</text>
</svg>
```

- [ ] **Step 2: Manifest** (`frontend/manifest.webmanifest`)

```json
{
  "name": "Hòa Tiến AI · Trợ lý hành chính số",
  "short_name": "Hòa Tiến AI",
  "start_url": "./index.html",
  "display": "standalone",
  "background_color": "#faf7ef",
  "theme_color": "#2f7d4f",
  "lang": "vi",
  "icons": [{ "src": "icons/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any" }]
}
```

- [ ] **Step 3: Service worker** (`frontend/sw.js`) — cache-first cho shell tĩnh, KHÔNG đụng API (khác origin nên tự bỏ qua):

```js
const CACHE = 'hoatien-shell-v1';
const SHELL = ['./', './index.html', './css/style.css', './js/api.js', './js/app.js', './manifest.webmanifest', './icons/icon.svg'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (url.origin !== location.origin || e.request.method !== 'GET') return; // API backend đi thẳng mạng
  e.respondWith(
    fetch(e.request).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(e.request, copy));
      return res;
    }).catch(() => caches.match(e.request))
  );
});
```

(Network-first cho shell: khi deploy bản mới người dùng nhận ngay, mất mạng mới rơi về cache — hợp yêu cầu "mất mạng vẫn mở được shell".)

- [ ] **Step 4: index.html** — trong `<head>` (sau viewport):

```html
<link rel="icon" href="icons/icon.svg" type="image/svg+xml" />
<link rel="manifest" href="manifest.webmanifest" />
<meta name="theme-color" content="#2f7d4f" />
```

Cuối body (sau script app.js):

```html
<script>
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js');
</script>
```

- [ ] **Step 5: Verify** — reload: tab có favicon HT. DevTools → Application: Manifest hợp lệ (installable), Service Worker activated. Chọn "Offline" trong DevTools → reload → shell vẫn mở, banner mất mạng của chat hiện (đúng thiết kế).

- [ ] **Step 6: Commit**

```bash
git add frontend/icons/icon.svg frontend/manifest.webmanifest frontend/sw.js frontend/index.html
git commit -m "feat: favicon + PWA manifest + offline shell service worker"
```

---

### Task 12: Frontend — a11y modal: focus trap + trả focus + ARIA

**Files:**
- Modify: `frontend/index.html` (2 modal: role/aria)
- Modify: `frontend/js/app.js` (helper trap + hook vào open/close 4 hàm)

- [ ] **Step 1: index.html** — thêm attributes:

```html
<div class="modal-bg" id="modalBg" role="dialog" aria-modal="true" aria-label="Chi tiết thủ tục" onclick="if(event.target===this)closeModal()">
...
<div class="modal-bg" id="authModalBg" role="dialog" aria-modal="true" aria-label="Đăng nhập hoặc đăng ký" onclick="if(event.target===this)closeAuthModal()">
```

- [ ] **Step 2: app.js — helper focus trap** (section mới trước phần Modal):

```js
/* ---------- Focus trap cho modal (a11y) ---------- */
let _lastFocused = null;
function trapFocus(bgEl) {
  _lastFocused = document.activeElement;
  const focusables = () => bgEl.querySelectorAll('button, a[href], input, [tabindex]:not([tabindex="-1"])');
  const first = focusables()[0];
  if (first) first.focus();
  bgEl.onkeydown = (e) => {
    if (e.key !== 'Tab') return;
    const list = Array.from(focusables()).filter(el => el.offsetParent !== null);
    if (!list.length) return;
    const firstEl = list[0], lastEl = list[list.length - 1];
    if (e.shiftKey && document.activeElement === firstEl) { e.preventDefault(); lastEl.focus(); }
    else if (!e.shiftKey && document.activeElement === lastEl) { e.preventDefault(); firstEl.focus(); }
  };
}
function releaseFocus(bgEl) {
  bgEl.onkeydown = null;
  if (_lastFocused) { _lastFocused.focus(); _lastFocused = null; }
}
```

- [ ] **Step 3: Hook vào 4 hàm open/close:**

- `openModal(p)`: sau `classList.add('show')` → `trapFocus(document.getElementById('modalBg'));`
- `closeModal()`: sau `classList.remove('show')` → `releaseFocus(document.getElementById('modalBg'));`
- `openAuthModal(tab)`: sau `classList.add('show')` → `trapFocus(document.getElementById('authModalBg'));` (đặt SAU `switchAuthTab(tab)` để focus vào input đang hiển thị)
- `closeAuthModal()`: tương tự với `authModalBg`.

- [ ] **Step 4: Verify** — mở modal thủ tục: Tab xoay vòng trong modal (không thoát ra trang sau), Shift+Tab ngược, Escape đóng (đã có sẵn), focus trả về card đã click. Modal auth tương tự, focus đầu vào nút ✕/tab đăng nhập.

- [ ] **Step 5: Commit**

```bash
git add frontend/index.html frontend/js/app.js
git commit -m "feat: modal accessibility - focus trap, focus restore, ARIA dialog"
```

---

### Task 13: Frontend — trang thống kê cho cán bộ xã (modal admin)

**Files:**
- Modify: `frontend/index.html` (nút trong user-dropdown + modal stats)
- Modify: `frontend/js/app.js`
- Modify: `frontend/css/style.css`

**Interfaces:**
- Consumes: `api.getAdminStats()` (Task 4), `getStoredUser().role` (đã có trong session).

- [ ] **Step 1: index.html** — trong `#userDropdown`, TRƯỚC nút logout:

```html
        <button id="statsBtn" style="display:none;">📊 Thống kê câu hỏi</button>
```

Modal mới (sau modal auth, trước script):

```html
<!-- MODAL: thống kê (admin) -->
<div class="modal-bg" id="statsModalBg" role="dialog" aria-modal="true" aria-label="Thống kê câu hỏi" onclick="if(event.target===this)closeStatsModal()">
  <div class="modal">
    <div class="modal-top">
      <button class="x" onclick="closeStatsModal()">✕</button>
      <div class="cat">Dành cho cán bộ xã</div>
      <h3>Người dân đang hỏi gì?</h3>
    </div>
    <div class="modal-body" id="statsBody"></div>
  </div>
</div>
```

- [ ] **Step 2: app.js — render stats** (section mới sau AUTH):

```js
/* ---------- Thống kê (admin) ---------- */
async function openStatsModal() {
  document.getElementById('userDropdown').classList.remove('show');
  const bg = document.getElementById('statsModalBg');
  const body = document.getElementById('statsBody');
  bg.classList.add('show');
  trapFocus(bg);
  body.innerHTML = '<p style="color:var(--ink-soft);">Đang tải…</p>';
  try {
    const s = await api.getAdminStats();
    const pctHelpful = (s.helpful + s.unhelpful) ? Math.round(100 * s.helpful / (s.helpful + s.unhelpful)) : null;
    body.innerHTML = `
      <div class="info-pills">
        <div class="pill"><b>Tổng câu hỏi</b>${s.total}</div>
        <div class="pill"><b>Trả lời được</b>${s.matched}</div>
        <div class="pill"><b>Chưa trả lời được</b>${s.unmatched}</div>
        <div class="pill"><b>Đánh giá hữu ích</b>${pctHelpful === null ? 'Chưa có' : pctHelpful + '% (' + (s.helpful + s.unhelpful) + ' lượt)'}</div>
      </div>
      <h4>Thủ tục được hỏi nhiều nhất</h4>
      ${s.top_procedures.length ? `<ul>${s.top_procedures.map(t => `<li><b>${t.count}×</b> — ${t.name}</li>`).join('')}</ul>` : '<p style="color:var(--ink-soft);">Chưa có dữ liệu.</p>'}
      <h4>Câu hỏi chưa trả lời được (gần nhất)</h4>
      ${s.recent_unmatched.length ? `<ul class="unmatched-list">${s.recent_unmatched.map(u => `<li>“${u.question}” <small>${new Date(u.created_at).toLocaleString('vi-VN')}</small></li>`).join('')}</ul>` : '<p style="color:var(--ink-soft);">Không có — trợ lý trả lời được hết 🎉</p>'}
      <p style="font-size:12px; color:var(--ink-soft); margin-top:14px;">Dùng danh sách này để bổ sung thủ tục/FAQ còn thiếu — trợ lý sẽ “học” thêm ngay khi cập nhật dữ liệu.</p>`;
  } catch (e) {
    body.innerHTML = '<p style="color:var(--ink-soft);">Không tải được thống kê. Bạn cần tài khoản admin.</p>';
  }
}
function closeStatsModal() {
  document.getElementById('statsModalBg').classList.remove('show');
  releaseFocus(document.getElementById('statsModalBg'));
}
```

Trong `updateAuthUI()` — nhánh `if (user)`: `document.getElementById('statsBtn').style.display = user.role === 'admin' ? 'block' : 'none';` (nhánh else đã ẩn dropdown). Trong `DOMContentLoaded`: `document.getElementById('statsBtn').onclick = openStatsModal;`. Thêm `closeStatsModal()` vào handler Escape chung.

- [ ] **Step 3: CSS**

```css
  /* ── Thống kê admin ── */
  .unmatched-list li { font-size:13.5px; margin:6px 0; }
  .unmatched-list small { color:var(--ink-soft); font-size:11px; display:block; }
```

- [ ] **Step 4: Verify** — đăng nhập admin → dropdown có "📊 Thống kê câu hỏi" → mở modal thấy số liệu khớp DB; đăng nhập user thường → không thấy nút; user thường gọi tay `api.getAdminStats()` trong console → lỗi 403.

- [ ] **Step 5: Commit**

```bash
git add frontend/index.html frontend/js/app.js frontend/css/style.css
git commit -m "feat: admin stats modal - top questions, unmatched, feedback rate"
```

---

## Ghi chú deploy (sau khi merge)

- Railway tự chạy migration? Nếu không, chạy `alembic upgrade head` trên production trước khi deploy code mới (cột `feedback_helpful`). Code cũ không đọc cột mới nên migration trước / code sau là an toàn.
- Frontend Vercel: `sw.js` cần được serve từ root scope của site — Vercel serve `frontend/` làm root nên OK.
- Đổi `CACHE = 'hoatien-shell-v2'` khi cần force refresh cache PWA ở lần deploy sau.
