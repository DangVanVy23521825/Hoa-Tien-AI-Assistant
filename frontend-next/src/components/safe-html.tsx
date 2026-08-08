"use client";

import { useEffect, useRef } from "react";
import { sanitizeHtml } from "@/lib/sanitize";

/** Render HTML của câu trả lời sau khi đã lọc allowlist thẻ.
    Phải ghi innerHTML trong useEffect: sanitizeHtml cần DOM (không chạy được lúc
    prerender), và React không ghi đè nội dung dangerouslySetInnerHTML khi hydrate
    — làm thẳng trong JSX sẽ ra bong bóng rỗng. */
export default function SafeHtml({
  html,
  className,
}: {
  html: string;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) ref.current.innerHTML = sanitizeHtml(html);
  }, [html]);

  return <div ref={ref} className={className} />;
}
