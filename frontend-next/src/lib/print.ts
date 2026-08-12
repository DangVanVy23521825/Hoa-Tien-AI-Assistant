import { Procedure } from "@/lib/api";

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/** Đổ checklist hồ sơ vào #printArea (con trực tiếp của <body>, xem app/layout.tsx)
    rồi gọi window.print(). CSS @media print ẩn mọi anh em của #printArea. */
export function printChecklist(procedure: Procedure) {
  const printArea = document.getElementById("printArea");
  if (!printArea) return;

  printArea.innerHTML = `
    <h1>UBND xã Hòa Tiến — Checklist hồ sơ</h1>
    <h2>${escapeHtml(procedure.name)}</h2>
    <p>${escapeHtml(procedure.description)}</p>
    <h3>Hồ sơ cần chuẩn bị (đánh dấu khi đã có):</h3>
    <ul>${procedure.documents.map((d) => `<li>☐ ${escapeHtml(d)}</li>`).join("")}</ul>
    <p><b>Lệ phí:</b> ${escapeHtml(procedure.fee)} — <b>Thời gian xử lý:</b> ${escapeHtml(procedure.processing_time)}</p>
    <p><b>Nơi nộp:</b> ${escapeHtml(procedure.place_of_submission)}</p>
    <p><b>Nộp trực tuyến:</b> ${escapeHtml(procedure.online_url)}</p>
    <p class="print-foot">In từ Trợ lý AI xã Hòa Tiến (Hòa Tiến AI) · ${new Date().toLocaleDateString("vi-VN")} · Thông tin tham khảo, đối soát tại Bộ phận Một cửa.</p>`;

  window.print();
}
