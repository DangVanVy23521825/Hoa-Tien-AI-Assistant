/* Làm sạch HTML do LLM sinh ra trước khi render.
   Câu hỏi của người dân đi thẳng vào prompt Gemini, còn câu trả lời được render
   bằng dangerouslySetInnerHTML — nên phải chặn allowlist thẻ/thuộc tính ở đây,
   nếu không một câu hỏi dạng prompt-injection có thể khiến mô hình trả về
   <img onerror=...> và đánh cắp JWT trong localStorage. */

const ALLOWED_TAGS = new Set([
  "B", "STRONG", "I", "EM", "U", "BR", "P", "UL", "OL", "LI", "SPAN", "SMALL", "CODE",
]);

/** Trả về chuỗi HTML chỉ còn các thẻ định dạng an toàn, không thuộc tính nào. */
export function sanitizeHtml(html: string): string {
  if (typeof window === "undefined") return "";

  const template = document.createElement("template");
  template.innerHTML = html;

  const walk = (node: Node) => {
    for (const child of Array.from(node.childNodes)) {
      if (child.nodeType === Node.TEXT_NODE) continue;

      if (child.nodeType !== Node.ELEMENT_NODE) {
        child.remove();
        continue;
      }

      const el = child as Element;
      if (!ALLOWED_TAGS.has(el.tagName)) {
        // Giữ lại phần chữ bên trong, chỉ bỏ thẻ.
        el.replaceWith(...Array.from(el.childNodes));
        continue;
      }

      for (const attr of Array.from(el.attributes)) {
        el.removeAttribute(attr.name);
      }
      walk(el);
    }
  };

  walk(template.content);
  return template.innerHTML;
}

/** Bỏ hết thẻ, chỉ lấy chữ — dùng khi cần so khớp hoặc hiển thị thuần văn bản. */
export function stripTags(html: string): string {
  if (typeof window === "undefined") return html;
  const el = document.createElement("div");
  el.innerHTML = html;
  return el.textContent || "";
}
