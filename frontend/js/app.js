/* ============================================================
   app.js — Logic UI Hòa Tiến AI Assistant (gọi backend thật)
   ============================================================ */

let CONTACTS = null;
let PROCEDURES = [];

/* ---------- QR helper ---------- */
function qr(data, size = 96) {
  return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&margin=0&data=${encodeURIComponent(data)}`;
}

/* ---------- Banner mạng ---------- */
function showNetBanner(show) {
  document.getElementById('netBanner').classList.toggle('show', show);
}

/* ---------- Chat UI ---------- */
function addMsg(role, contentHtml, src) {
  const body = document.getElementById('chatBody');
  const wrap = document.createElement('div');
  wrap.className = 'msg ' + role;
  const av = role === 'bot' ? 'AI' : 'Bạn';
  wrap.innerHTML = `<div class="mini-av">${av}</div>
    <div class="bubble">${contentHtml}${src ? `<div class="src"><b>ⓘ</b> ${src}</div>` : ''}</div>`;
  body.appendChild(wrap);
  body.scrollTop = body.scrollHeight;
  return wrap;
}

function addTyping() {
  const body = document.getElementById('chatBody');
  const w = document.createElement('div');
  w.className = 'msg bot'; w.id = 'typingRow';
  w.innerHTML = `<div class="mini-av">AI</div><div class="bubble typing"><span></span><span></span><span></span></div>`;
  body.appendChild(w); body.scrollTop = body.scrollHeight;
}
function removeTyping() { const t = document.getElementById('typingRow'); if (t) t.remove(); }

function buildAnswerHtml(res) {
  let html = res.answer_html;
  // Thủ tục → kèm QR nộp hồ sơ trực tuyến (backend trả online_url, style .qr-inline có sẵn)
  if (res.matched_source_type === 'procedure' && res.online_url) {
    html += `<div class="qr-inline">
      <img src="${qr(res.online_url, 74)}" alt="QR nộp trực tuyến"/>
      <small>Quét mã để nộp hồ sơ trực tuyến qua Cổng Dịch vụ công.<br/>Xem chi tiết trong mục “Thủ tục”.</small>
    </div>`;
  }
  return html;
}

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

let askInFlight = false;

async function ask(query) {
  if (!query.trim() || askInFlight) return;
  askInFlight = true;
  addMsg('user', query);
  document.getElementById('chatInput').value = '';
  addTyping();
  try {
    const res = await api.chat(query);
    removeTyping();
    const botMsg = addMsg('bot', buildAnswerHtml(res), res.source);
    addFeedbackBar(botMsg, res.message_id);
    if (res.matched_source_type === 'procedure' && res.matched_source_id) {
      const pr = document.createElement('button');
      pr.className = 'print-btn';
      pr.innerHTML = '🖨️ In checklist hồ sơ';
      pr.onclick = () => printChecklist(res.matched_source_id);
      botMsg.querySelector('.bubble').appendChild(pr);
    }
    showNetBanner(false);
    // Chỉ reload panel lịch sử khi nó đang mở
    if (getToken() && document.getElementById('historyPanel').classList.contains('show')) loadHistory();
  } catch (e) {
    removeTyping();
    if (e instanceof ApiError && e.status === 0) {
      showNetBanner(true);
      addMsg('bot', 'Không kết nối được tới máy chủ. Vui lòng thử lại sau ít phút.');
    } else {
      addMsg('bot', 'Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.');
    }
  } finally {
    askInFlight = false;
  }
}

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

/* ---------- Khởi tạo dữ liệu tĩnh (procedures, faq, contacts) ---------- */
async function initData() {
  try {
    const [procedures, faqs, contacts] = await Promise.all([
      api.getProcedures(), api.getFaq(), api.getContacts(),
    ]);
    PROCEDURES = procedures;
    CONTACTS = contacts;
    renderProcedures(procedures);
    renderFaq(faqs);
    renderContacts(contacts);
    showNetBanner(false);
  } catch (e) {
    showNetBanner(true);
  }
}

function renderProcedures(procedures) {
  const grid = document.getElementById('procGrid');
  grid.innerHTML = '';
  procedures.forEach(p => {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <div class="arrow"><svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
      <div class="cat">${p.category}</div>
      <h3>${p.name}</h3>
      <p>${p.description}</p>
      <div class="meta"><span><b>Phí:</b> ${p.fee.split('(')[0]}</span><span><b>⏱</b> ${p.processing_time}</span></div>`;
    card.onclick = () => openModal(p);
    grid.appendChild(card);
  });
}

function renderFaq(faqs) {
  const faqList = document.getElementById('faqList');
  faqList.innerHTML = '';
  faqs.forEach(f => {
    const item = document.createElement('div');
    item.className = 'faq-item';
    item.innerHTML = `<div class="faq-q">${f.question}<span class="ic"><svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg></span></div>
      <div class="faq-a">${f.answer}</div>`;
    item.querySelector('.faq-q').onclick = () => item.classList.toggle('open');
    faqList.appendChild(item);
  });
}

function renderContacts(c) {
  const rows = [
    ['📍', 'Địa chỉ', c.address],
    ['☎️', 'Điện thoại', c.phone],
    ['🕒', 'Giờ làm việc', c.working_hours.weekdays],
    ['🌐', 'Cổng thông tin', c.portal_url],
  ];
  const cl = document.getElementById('contactList');
  cl.innerHTML = '';
  rows.forEach(([ic, label, val]) => {
    const r = document.createElement('div');
    r.className = 'contact-row';
    r.innerHTML = `<div class="ci">${ic}</div><div><b>${label}</b><span>${val}</span></div>`;
    cl.appendChild(r);
  });
  document.getElementById('portalQr').src = qr(c.portal_url, 150);
}

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

/* ---------- Modal chi tiết thủ tục ---------- */
function openModal(p) {
  const m = document.getElementById('modalContent');
  m.innerHTML = `
    <div class="modal-top">
      <button class="x" onclick="closeModal()">✕</button>
      <div class="cat">${p.category}</div>
      <h3>${p.name}</h3>
    </div>
    <div class="modal-body">
      <p style="color:var(--ink-soft);">${p.description}</p>
      <h4>Hồ sơ cần chuẩn bị</h4>
      <ul>${p.documents.map(d => `<li>${d}</li>`).join('')}</ul>
      <h4>Thông tin xử lý</h4>
      <div class="info-pills">
        <div class="pill"><b>Lệ phí</b>${p.fee}</div>
        <div class="pill"><b>Thời gian</b>${p.processing_time}</div>
        <div class="pill"><b>Nơi nộp</b>${p.place_of_submission}</div>
        <div class="pill"><b>Căn cứ</b>${p.legal_basis}</div>
      </div>
      <div class="qr-box">
        <img src="${qr(p.online_url, 96)}" alt="QR nộp trực tuyến"/>
        <div><b>Nộp hồ sơ trực tuyến</b><br/><small>Quét mã QR để đến Cổng Dịch vụ công Quốc gia và nộp hồ sơ ${p.name.toLowerCase()}.</small></div>
      </div>
      <button class="btn btn-ghost modal-cta" onclick="printChecklist('${p.code}')">🖨️ In checklist hồ sơ</button>
      <a href="#tro-ly" class="btn btn-primary modal-cta" onclick="closeModal()">Hỏi trợ lý về thủ tục này →</a>
    </div>`;
  document.getElementById('modalBg').classList.add('show');
  trapFocus(document.getElementById('modalBg'));
}
function closeModal() {
  const bg = document.getElementById('modalBg');
  if (!bg.classList.contains('show')) return; // Escape gọi mọi hàm close — bỏ qua modal đang đóng
  bg.classList.remove('show');
  releaseFocus(bg);
}

/* ============================================================
   AUTH
   ============================================================ */
function openAuthModal(tab = 'login') {
  document.getElementById('authModalBg').classList.add('show');
  switchAuthTab(tab);
  document.getElementById('authError').classList.remove('show');
  // trap SAU switchAuthTab để focus rơi vào input của form đang hiển thị
  trapFocus(document.getElementById('authModalBg'));
}
function closeAuthModal() {
  const bg = document.getElementById('authModalBg');
  if (!bg.classList.contains('show')) return;
  bg.classList.remove('show');
  releaseFocus(bg);
}

function switchAuthTab(tab) {
  document.querySelectorAll('.auth-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
  document.getElementById('loginForm').classList.toggle('active', tab === 'login');
  document.getElementById('registerForm').classList.toggle('active', tab === 'register');
}

function showAuthError(msg) {
  const el = document.getElementById('authError');
  el.textContent = msg;
  el.classList.add('show');
}

function updateAuthUI() {
  const user = getStoredUser();
  const trigger = document.getElementById('authTrigger');
  const dropdown = document.getElementById('userDropdown');
  const historyToggle = document.getElementById('historyToggle');

  if (user) {
    trigger.innerHTML = `<span class="av">${user.display_name.charAt(0).toUpperCase()}</span> ${user.display_name.split(' ')[0]}`;
    document.getElementById('userName').textContent = user.display_name;
    document.getElementById('userEmail').textContent = user.email;
    historyToggle.style.display = 'inline-flex';
  } else {
    trigger.textContent = 'Đăng nhập';
    dropdown.classList.remove('show');
    historyToggle.style.display = 'none';
    document.getElementById('historyPanel').classList.remove('show');
  }
}

async function loadHistory() {
  const panel = document.getElementById('historyPanel');
  try {
    const items = await api.getHistory();
    if (!items.length) {
      panel.innerHTML = '<div style="color:var(--ink-soft); font-size:13px;">Bạn chưa có câu hỏi nào được lưu.</div>';
      return;
    }
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
  } catch (e) {
    panel.innerHTML = '<div style="color:var(--ink-soft); font-size:13px;">Không tải được lịch sử.</div>';
  }
}

/* ---------- Events ---------- */
document.addEventListener('DOMContentLoaded', () => {
  initData();
  updateAuthUI();
  initVoiceInput();
  initShare();

  // greeting + chips
  addMsg('bot', `Xin chào 👋 Tôi là trợ lý hành chính số của <b>xã Hòa Tiến</b>. Bạn cần tra cứu thủ tục nào? Ví dụ: khai sinh, kết hôn, chứng thực, giờ làm việc…`);
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

  // Chips động theo thủ tục được hỏi nhiều + social proof — lỗi thì giữ mặc định.
  // Ngưỡng: >=3 chips để không hiện lẻ loi, >=10 câu để hero không khoe con số quá nhỏ.
  api.getPublicStats().then(s => {
    if (s.top_questions && s.top_questions.length >= 3) renderChips(s.top_questions);
    if (s.total_answered >= 10) {
      document.getElementById('statAnsweredNum').textContent = s.total_answered.toLocaleString('vi-VN');
      document.getElementById('statAnswered').style.display = '';
    }
  }).catch(() => {});

  document.getElementById('sendBtn').onclick = () => ask(document.getElementById('chatInput').value);
  document.getElementById('chatInput').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.isComposing && e.keyCode !== 229) {
      e.preventDefault();
      ask(e.target.value);
    }
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') { closeModal(); closeAuthModal(); } });

  // Auth trigger
  document.getElementById('authTrigger').onclick = () => {
    if (getStoredUser()) {
      document.getElementById('userDropdown').classList.toggle('show');
    } else {
      openAuthModal('login');
    }
  };
  document.getElementById('logoutBtn').onclick = () => {
    clearSession();
    updateAuthUI();
    document.getElementById('userDropdown').classList.remove('show');
  };
  document.querySelectorAll('.auth-tab').forEach(t => t.onclick = () => switchAuthTab(t.dataset.tab));

  document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    document.getElementById('authError').classList.remove('show');
    try {
      const res = await api.login(
        document.getElementById('loginEmail').value,
        document.getElementById('loginPassword').value
      );
      setSession(res.access_token, res.user);
      updateAuthUI();
      closeAuthModal();
    } catch (err) {
      showAuthError(err instanceof ApiError && err.status === 0 ? 'Không kết nối được máy chủ.' : err.message);
    }
  });

  document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    document.getElementById('authError').classList.remove('show');
    try {
      const res = await api.register(
        document.getElementById('registerEmail').value,
        document.getElementById('registerPassword').value,
        document.getElementById('registerName').value
      );
      setSession(res.access_token, res.user);
      updateAuthUI();
      closeAuthModal();
    } catch (err) {
      showAuthError(err instanceof ApiError && err.status === 0 ? 'Không kết nối được máy chủ.' : err.message);
    }
  });

  document.getElementById('historyToggle').onclick = () => {
    const panel = document.getElementById('historyPanel');
    panel.classList.toggle('show');
    if (panel.classList.contains('show')) loadHistory();
  };
});
