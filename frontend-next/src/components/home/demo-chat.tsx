"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Send, RotateCcw, BookText } from "lucide-react";
import MascotAvatar from "@/components/mascot-avatar";

/* Demo có kịch bản, KHÔNG gọi API.
   Lý do: đây là thứ đầu tiên giám khảo/người dân nhìn thấy — nó phải hiện ra tức thì và
   vẫn chạy khi mạng hội trại kém hoặc backend sập (nguyên tắc kiến trúc #4). Nội dung
   dưới đây chép đúng dữ liệu thủ tục KS-01 trong knowledge base, nên không phải "ảnh
   chụp đẹp hơn sự thật" — hỏi lại trong trợ lý sẽ ra đúng những mục này.
   Ô nhập bên dưới là thật: gõ câu hỏi sẽ chuyển sang /tro-ly và hỏi backend. */

const DEMO_QUESTION = "Tôi muốn đăng ký khai sinh cho con";

const DEMO_DOCS = [
  "Tờ khai đăng ký khai sinh (theo mẫu)",
  "Giấy chứng sinh do cơ sở y tế cấp",
  "Giấy tờ tùy thân của cha, mẹ (CCCD/hộ chiếu)",
  "Giấy chứng nhận kết hôn của cha mẹ (nếu có)",
];

const DEMO_META = [
  { label: "Lệ phí", value: "Miễn phí (đăng ký đúng hạn)" },
  { label: "Thời gian", value: "Trong ngày làm việc" },
  { label: "Nơi nộp", value: "Trung tâm Phục vụ hành chính công xã Hòa Tiến" },
];

const DEMO_SOURCE = "Danh mục thủ tục xã Hòa Tiến · Luật Hộ tịch 2014; Nghị định 123/2015/NĐ-CP";

/** 0 chưa bắt đầu · 1 hiện câu hỏi · 2 đang gõ · 3 hiện câu trả lời */
type Stage = 0 | 1 | 2 | 3;

export default function DemoChat() {
  const [stage, setStage] = useState<Stage>(0);
  const [input, setInput] = useState("");
  const router = useRouter();
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  /** Người bật "giảm chuyển động" nhận thẳng trạng thái cuối (mọi mốc cùng ở 0ms). */
  const play = () => {
    timers.current.forEach(clearTimeout);
    const reduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const steps: [Stage, number][] = reduced
      ? [[3, 0]]
      : [
          [0, 0],
          [1, 500],
          [2, 1300],
          [3, 2500],
        ];
    timers.current = steps.map(([s, d]) => setTimeout(() => setStage(s), d));
  };

  useEffect(() => {
    play();
    return () => timers.current.forEach(clearTimeout);
  }, []);

  const handleAsk = () => {
    const q = input.trim();
    router.push(q ? `/tro-ly?q=${encodeURIComponent(q)}` : "/tro-ly");
  };

  return (
    <div
      ref={containerRef}
      className="bg-white border border-line rounded-2xl shadow-xl overflow-hidden"
    >
      <div className="flex items-center gap-3 px-4 py-3 border-b border-line bg-gradient-to-r from-paddy-deep to-river-deep text-white">
        <MascotAvatar size={32} className="ring-white/25" />
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm">Trợ lý Hòa Tiến</div>
          <div className="text-[11px] opacity-85 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#7ee6a1] animate-pulse-dot" />
            Trả lời trong phạm vi dữ liệu xã
          </div>
        </div>
        <button
          onClick={play}
          className="text-white/85 hover:text-white text-[11px] font-semibold inline-flex items-center gap-1"
          aria-label="Xem lại minh hoạ"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Xem lại
        </button>
      </div>

      <div className="p-4 flex flex-col gap-3 min-h-[352px]">
        {stage >= 1 && (
          <div className="self-end flex gap-2 max-w-[86%] animate-rise">
            <div className="bg-paddy text-white rounded-2xl rounded-tr-sm px-3.5 py-2.5 text-sm">
              {DEMO_QUESTION}
            </div>
            <div className="w-7 h-7 rounded-lg bg-rice text-ink grid place-items-center text-[11px] font-bold flex-shrink-0">
              Bạn
            </div>
          </div>
        )}

        {stage === 2 && (
          <div className="self-start flex gap-2 animate-rise">
            <MascotAvatar />
            <div className="px-3.5 py-3 rounded-2xl rounded-tl-sm bg-[#f1f4ef] border border-[#e2e9df]">
              <span className="flex gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-[#9fb0a3] typing-dot" />
                <span className="w-1.5 h-1.5 rounded-full bg-[#9fb0a3] typing-dot" />
                <span className="w-1.5 h-1.5 rounded-full bg-[#9fb0a3] typing-dot" />
              </span>
            </div>
          </div>
        )}

        {stage === 3 && (
          <div className="self-start flex gap-2 max-w-[94%] animate-rise">
            <MascotAvatar />
            <div className="px-3.5 py-3 rounded-2xl rounded-tl-sm bg-[#f1f4ef] border border-[#e2e9df] text-sm">
              <p className="font-semibold text-ink">Hồ sơ bạn cần chuẩn bị:</p>
              <ol className="mt-2 space-y-1.5">
                {DEMO_DOCS.map((d, i) => (
                  <li key={d} className="flex gap-2">
                    <span className="w-4 h-4 mt-0.5 rounded bg-paddy/12 text-paddy-deep text-[10px] font-bold grid place-items-center flex-shrink-0">
                      {i + 1}
                    </span>
                    <span className="text-ink-soft">{d}</span>
                  </li>
                ))}
              </ol>

              <dl className="mt-3 pt-3 border-t border-dashed border-[#cdd8c9] space-y-1">
                {DEMO_META.map((m) => (
                  <div key={m.label} className="flex gap-2 text-xs">
                    <dt className="font-semibold text-paddy-deep flex-shrink-0">
                      {m.label}:
                    </dt>
                    <dd className="text-ink-soft">{m.value}</dd>
                  </div>
                ))}
              </dl>

              <div className="mt-3 pt-2.5 border-t border-dashed border-[#cdd8c9] flex gap-1.5 text-xs text-ink-soft">
                <BookText className="w-3.5 h-3.5 text-paddy-deep flex-shrink-0 mt-0.5" />
                <span>
                  <span className="font-semibold text-paddy-deep">Nguồn:</span>{" "}
                  {DEMO_SOURCE}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="flex gap-2 p-3 border-t border-line bg-[#fbfaf5]">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.nativeEvent.isComposing) handleAsk();
          }}
          placeholder="Hỏi câu của bạn…"
          aria-label="Hỏi trợ lý câu của bạn"
          className="flex-1 min-w-0 bg-white border border-line rounded-xl px-3.5 py-2.5 text-sm outline-none focus:border-paddy focus:ring-2 focus:ring-paddy/10"
        />
        <button
          onClick={handleAsk}
          aria-label="Gửi câu hỏi cho trợ lý"
          className="bg-paddy hover:bg-paddy-deep text-white rounded-xl px-3.5 grid place-items-center transition-colors flex-shrink-0"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
