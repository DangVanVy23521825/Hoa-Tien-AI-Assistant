"use client";

import { useState, useRef, useEffect } from "react";
import { api, ApiError, qr, Procedure } from "@/lib/api";
import { stripTags } from "@/lib/sanitize";
import SafeHtml from "@/components/safe-html";
import MascotAvatar from "@/components/mascot-avatar";
import { printChecklist } from "@/lib/print";
import { useAuth } from "@/components/auth-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { Send, Mic, Printer, ThumbsUp, ThumbsDown, History, AlertCircle, Lock } from "lucide-react";

interface Message {
  role: "user" | "bot";
  content: string;
  html?: string;
  source?: string;
  messageId?: string | null;
  matchedType?: string | null;
  matchedId?: string | null;
  onlineUrl?: string | null;
}

/**
 * Câu gợi ý mặc định — viết thành câu hỏi hoàn chỉnh để người dân bấm là hiểu
 * ngay mình đang hỏi gì. Cả 5 câu đều đã kiểm trên API thật và khớp dữ liệu
 * (procedure/faq/contact); đừng thêm câu nào chưa thử, chip rơi vào câu từ chối
 * là mất điểm ngay trước mặt người dùng.
 */
const DEFAULT_CHIPS = [
  "Đăng ký khai sinh cần giấy tờ gì?",
  "Mất CCCD thì làm lại ở đâu?",
  "Đăng ký thường trú ở đâu?",
  "Cần giấy tờ gì để chứng thực bản sao?",
  "UBND xã làm việc giờ nào?",
];

export default function TroLyPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "bot",
      content:
        "Xin chào 👋 Tôi là Trợ lý AI xã Hòa Tiến. Bạn muốn hỏi gì ạ? Ví dụ: khai sinh, chứng thực, giờ làm việc, hay lịch sử — văn hóa — làng nghề của xã…",
      html:
        "Xin chào 👋 Tôi là <b>Trợ lý AI xã Hòa Tiến</b>. Bạn muốn hỏi gì ạ? Ví dụ: khai sinh, chứng thực, giờ làm việc, hay lịch sử — văn hóa — làng nghề của xã…",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [chips, setChips] = useState<string[]>(DEFAULT_CHIPS);
  const [networkError, setNetworkError] = useState(false);
  const [history, setHistory] = useState<{ question: string; answer: string; created_at: string }[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [listening, setListening] = useState(false);
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  // Hạn mức hỏi thử của khách chưa đăng nhập. null = chưa biết hoặc đã đăng nhập.
  const [turnsLeft, setTurnsLeft] = useState<number | null>(null);
  // Dẫn xuất chứ không phải state riêng: về 0 là chặn ngay, không để người dùng gõ
  // thêm một câu nữa rồi mới ăn lỗi 403.
  const quotaBlocked = !user && turnsLeft === 0;
  const chatBodyRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    api
      .getPublicStats()
      .then((s) => {
        // `top_questions` thực chất là TÊN thủ tục được hỏi nhiều nhất, không
        // phải câu hỏi: "Đăng ký biến động đất đai (chuyển nhượng, tặng cho,
        // thừa kế quyền sử dụng đất)" đắp nguyên vào chip thì vừa dài vừa không
        // ra một câu hỏi. Chỉ nhận khi backend trả đúng dạng câu hỏi ngắn, còn
        // lại giữ danh sách đã biên tập.
        const usable = (s.top_questions ?? []).filter(
          (q) => q.trim().endsWith("?") && q.length <= 52,
        );
        if (usable.length >= 3) setChips(usable);
      })
      .catch(() => {});

    // Nạp sẵn để nút "In checklist hồ sơ" dựng được nội dung in từ mã thủ tục
    // mà /chat trả về (response chat không kèm danh sách giấy tờ).
    api
      .getProcedures()
      .then(setProcedures)
      .catch(() => {});
  }, []);

  useEffect(() => {
    // Người đã đăng nhập không có hạn mức; badge và cổng chặn đều lọc theo `user`
    // nên không cần dọn state ở đây.
    if (user) return;
    api
      .getGuestQuota()
      .then((q) => setTurnsLeft(q.remaining))
      .catch(() => {});
  }, [user]);

  useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight;
    }
  }, [messages]);

  const ask = async (query: string) => {
    if (!query.trim() || loading || quotaBlocked) return;
    setLoading(true);
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setInput("");

    try {
      const res = await api.chat(query);
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          content: stripTags(res.answer_html),
          html: res.answer_html,
          source: res.source,
          messageId: res.message_id,
          matchedType: res.matched_source_type,
          matchedId: res.matched_source_id,
          onlineUrl: res.online_url,
        },
      ]);
      setNetworkError(false);
      setTurnsLeft(res.guest_turns_left);
    } catch (e) {
      if (e instanceof ApiError && e.code === "guest_quota_exceeded") {
        setTurnsLeft(0);
        setMessages((prev) => [
          ...prev,
          {
            role: "bot",
            content:
              "Bạn đã dùng hết lượt hỏi thử. Đăng ký tài khoản miễn phí để hỏi không giới hạn và lưu lại lịch sử câu hỏi của mình.",
          },
        ]);
      } else if (e instanceof ApiError && e.status === 0) {
        setNetworkError(true);
        setMessages((prev) => [
          ...prev,
          {
            role: "bot",
            content: "Không kết nối được tới máy chủ. Vui lòng thử lại sau ít phút.",
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "bot",
            content: "Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.",
          },
        ]);
      }
    } finally {
      setLoading(false);
    }
  };

  // Câu hỏi chuyển sang từ trang chủ (?q=...). Đọc từ window thay vì useSearchParams
  // để trang này vẫn được prerender tĩnh, không cần bọc Suspense.
  const handoffDone = useRef(false);
  useEffect(() => {
    if (handoffDone.current) return;
    handoffDone.current = true;
    const q = new URLSearchParams(window.location.search).get("q");
    if (q) {
      window.history.replaceState(null, "", "/tro-ly");
      // Chủ đích: hỏi ngay khi mount là toàn bộ mục đích của handoff từ trang chủ.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      ask(q);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.nativeEvent.isComposing) {
      e.preventDefault();
      ask(input);
    }
  };

  /* eslint-disable @typescript-eslint/no-explicit-any */
  const toggleVoice = () => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return;

    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }

    const rec = new SR();
    rec.lang = "vi-VN";
    rec.interimResults = true;
    recognitionRef.current = rec;

    rec.onresult = (e: any) => {
      const transcript = Array.from(e.results)
        .map((r: any) => r[0].transcript)
        .join("");
      setInput(transcript);
      if (e.results[e.results.length - 1].isFinal) {
        ask(transcript);
      }
    };
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);

    setListening(true);
    rec.start();
  };
  /* eslint-enable @typescript-eslint/no-explicit-any */

  const loadHistory = async () => {
    if (!user) return;
    try {
      const items = await api.getHistory();
      setHistory(items);
    } catch {
      setHistory([]);
    }
  };

  const handleFeedback = async (messageId: string, helpful: boolean) => {
    try {
      await api.sendFeedback(messageId, helpful);
    } catch {}
  };

  return (
    <section className="bg-gradient-to-b from-white/55 to-[#f7f3e8]/55 border-t border-b border-line py-14 px-6">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <Badge
            variant="secondary"
            className="mb-3 bg-river-deep/8 text-river-deep font-semibold tracking-wider uppercase text-xs px-3 py-1.5 rounded-full"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-paddy mr-2" />
            Trợ lý AI
          </Badge>
          <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight">
            Hỏi bất cứ điều gì về xã Hòa Tiến
          </h2>
          <p className="mt-2 text-ink-soft">
            Ví dụ: &ldquo;Làm khai sinh cho con cần giấy tờ gì?&rdquo; hay
            &ldquo;Đình làng Hương Lam có gì đặc biệt?&rdquo; — trợ lý trả lời
            kèm nguồn.
          </p>
        </div>

        <div className="bg-white border border-line rounded-2xl shadow-lg overflow-hidden flex flex-col h-[560px]">
          <div className="flex items-center gap-3 px-5 py-4 border-b border-line bg-gradient-to-r from-paddy-deep to-river-deep text-white">
            <MascotAvatar size={36} className="rounded-xl ring-white/25" />
            <div className="flex-1 min-w-0">
              <div className="font-semibold text-sm">Trợ lý AI xã Hòa Tiến</div>
              <div className="text-xs opacity-85 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#7ee6a1] animate-pulse-dot shrink-0" />
                {/* Vế sau ẩn trên điện thoại: để nguyên thì dòng này xuống 3
                    hàng, đội cao thanh tiêu đề và đè lên tin nhắn đầu tiên. */}
                <span className="truncate">
                  Đang trực tuyến
                  <span className="hidden sm:inline">
                    {" "}
                    · Trả lời trong phạm vi dữ liệu xã
                  </span>
                </span>
              </div>
            </div>
            {user ? (
              <button
                onClick={() => {
                  setShowHistory(!showHistory);
                  if (!showHistory) loadHistory();
                }}
                className="text-white text-xs font-semibold flex items-center gap-1 hover:underline"
              >
                <History className="w-3.5 h-3.5" />
                Lịch sử
              </button>
            ) : (
              turnsLeft !== null && (
                <span className="text-xs font-semibold bg-white/16 rounded-full px-2.5 py-1 whitespace-nowrap">
                  Còn {turnsLeft} lượt hỏi thử
                </span>
              )
            )}
          </div>

          {showHistory && history.length > 0 && (
            <div className="border-b border-line px-5 py-3 max-h-44 overflow-y-auto bg-[#fbfaf5]">
              {history.map((h, i) => (
                <div
                  key={i}
                  className="py-2 border-b border-dashed border-line last:border-0 cursor-pointer hover:text-paddy-deep text-sm"
                  onClick={() => {
                    setMessages((prev) => [
                      ...prev,
                      { role: "user", content: h.question },
                      {
                        role: "bot",
                        content: h.answer,
                        source:
                          "Từ lịch sử đã lưu · " +
                          new Date(h.created_at).toLocaleDateString("vi-VN"),
                      },
                    ]);
                    setShowHistory(false);
                  }}
                >
                  <div className="font-semibold">{h.question}</div>
                  <div className="text-xs text-ink-soft">
                    {new Date(h.created_at).toLocaleString("vi-VN")}
                  </div>
                </div>
              ))}
            </div>
          )}

          {networkError && (
            <div className="mx-5 mt-3 bg-[#fdf0ee] border border-[#f3d4cf] text-[#8a332e] text-sm px-4 py-2.5 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>
                Không kết nối được tới máy chủ. Vui lòng thử lại, hoặc dùng{" "}
                <a
                  href="/legacy/index.html"
                  className="font-semibold underline"
                >
                  bản tra cứu ngoại tuyến
                </a>{" "}
                (dữ liệu lưu sẵn trong máy).
              </span>
            </div>
          )}

          <div
            ref={chatBodyRef}
            className="flex-1 overflow-y-auto p-5 flex flex-col gap-4"
          >
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-2.5 max-w-[88%] ${
                  msg.role === "user"
                    ? "self-end flex-row-reverse"
                    : "self-start"
                }`}
              >
                {msg.role === "bot" ? (
                  <MascotAvatar />
                ) : (
                  <div className="w-7 h-7 rounded-lg grid place-items-center text-xs font-bold flex-shrink-0 bg-rice text-ink">
                    Bạn
                  </div>
                )}
                <div
                  className={`px-3.5 py-3 rounded-2xl text-[14.5px] ${
                    msg.role === "bot"
                      ? "bg-[#f1f4ef] border border-[#e2e9df] rounded-tl-sm"
                      : "bg-paddy text-white rounded-tr-sm"
                  }`}
                >
                  {msg.html ? (
                    <SafeHtml html={msg.html} />
                  ) : (
                    <p>{msg.content}</p>
                  )}
                  {msg.source && (
                    <div className="mt-2 pt-2 border-t border-dashed border-[#cdd8c9] text-xs text-ink-soft">
                      <span className="font-semibold text-paddy-deep">ⓘ</span>{" "}
                      {msg.source}
                    </div>
                  )}
                  {msg.role === "bot" && msg.messageId && (
                    <div className="mt-2 pt-2 border-t border-dashed border-line flex items-center gap-2 text-xs text-ink-soft">
                      <span>Câu trả lời có hữu ích?</span>
                      <button
                        onClick={() => handleFeedback(msg.messageId!, true)}
                        className="bg-white border border-line rounded-lg px-2 py-0.5 hover:border-paddy hover:scale-105 transition-transform"
                      >
                        <ThumbsUp className="w-3.5 h-3.5 inline" />
                      </button>
                      <button
                        onClick={() => handleFeedback(msg.messageId!, false)}
                        className="bg-white border border-line rounded-lg px-2 py-0.5 hover:border-paddy hover:scale-105 transition-transform"
                      >
                        <ThumbsDown className="w-3.5 h-3.5 inline" />
                      </button>
                    </div>
                  )}
                  {msg.matchedType === "procedure" && msg.onlineUrl && (
                    <div className="mt-2.5 flex items-center gap-3 bg-cream border border-line rounded-xl p-2.5">
                      <img
                        src={qr(msg.onlineUrl, 74)}
                        alt="QR nộp trực tuyến"
                        className="w-[74px] h-[74px] rounded-md"
                      />
                      <small className="text-xs text-ink-soft">
                        Quét mã để nộp hồ sơ trực tuyến qua Cổng Dịch vụ công.
                      </small>
                    </div>
                  )}
                  {msg.matchedType === "procedure" &&
                    msg.matchedId &&
                    procedures.some((p) => p.code === msg.matchedId) && (
                      <button
                        onClick={() => {
                          // /chat trả matched_source_id = code thủ tục ("KS-01"),
                          // không phải UUID id.
                          const p = procedures.find(
                            (x) => x.code === msg.matchedId
                          );
                          if (p) printChecklist(p);
                        }}
                        className="mt-2 inline-flex items-center gap-1 bg-white border border-line rounded-lg px-3 py-1.5 text-xs font-semibold hover:border-paddy hover:text-paddy-deep transition-colors"
                      >
                        <Printer className="w-3.5 h-3.5" />
                        In checklist hồ sơ
                      </button>
                    )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex gap-2.5 self-start">
                <MascotAvatar />
                <div className="px-3.5 py-3 rounded-2xl bg-[#f1f4ef] border border-[#e2e9df] rounded-tl-sm">
                  <span className="flex gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#9fb0a3] typing-dot" />
                    <span className="w-1.5 h-1.5 rounded-full bg-[#9fb0a3] typing-dot" />
                    <span className="w-1.5 h-1.5 rounded-full bg-[#9fb0a3] typing-dot" />
                  </span>
                </div>
              </div>
            )}
          </div>

          {quotaBlocked ? (
            <div className="border-t border-line p-5 bg-[#f6faf4]">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-xl bg-paddy/12 text-paddy-deep grid place-items-center flex-shrink-0">
                  <Lock className="w-4.5 h-4.5" />
                </div>
                <div className="flex-1">
                  <div className="font-bold text-[15px]">
                    Hết lượt hỏi thử miễn phí
                  </div>
                  <p className="text-sm text-ink-soft mt-0.5">
                    Đăng ký tài khoản (miễn phí, chỉ cần email) để hỏi không giới hạn
                    và xem lại toàn bộ lịch sử câu hỏi của bạn.
                  </p>
                  <div className="flex gap-2.5 mt-3">
                    <Link href="/dang-nhap">
                      <Button className="bg-paddy hover:bg-paddy-deep rounded-xl">
                        Đăng ký miễn phí
                      </Button>
                    </Link>
                    <Link href="/dang-nhap">
                      <Button
                        variant="outline"
                        className="rounded-xl border-line text-river-deep hover:border-paddy hover:text-paddy-deep"
                      >
                        Tôi đã có tài khoản
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          ) : (
          <>
          <div className="px-5 pt-3.5">
            <div className="text-xs font-semibold uppercase tracking-wider text-ink-soft mb-2">
              Bạn có thể hỏi:
            </div>
            <div className="flex gap-2 flex-wrap">
              {chips.map((chip, i) => (
                <button
                  key={chip}
                  onClick={() => ask(chip)}
                  /* Điện thoại chỉ hiện 3 câu: mỗi chip chiếm trọn một hàng,
                     để đủ 5 là ô nhập câu hỏi bị đẩy khỏi màn hình. */
                  className={`${i >= 3 ? "hidden sm:block" : ""} bg-white border border-line rounded-full px-3.5 py-2 text-[13px] font-medium text-ink-soft hover:border-paddy hover:text-paddy-deep hover:bg-[#f6faf4] transition-colors`}
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-2.5 p-4 border-t border-line">
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Nhập câu hỏi của bạn…"
              className="flex-1 border-line bg-[#fbfaf5] focus:border-paddy focus:bg-white focus:ring-2 focus:ring-paddy/10 rounded-xl"
            />
            <Button
              variant="outline"
              size="icon"
              onClick={toggleVoice}
              className={`rounded-xl border-line flex-shrink-0 ${
                listening
                  ? "bg-paddy text-white border-paddy animate-pulse"
                  : "text-river-deep hover:border-paddy hover:text-paddy-deep"
              }`}
              aria-label="Hỏi bằng giọng nói"
            >
              <Mic className="w-5 h-5" />
            </Button>
            <Button
              size="icon"
              onClick={() => ask(input)}
              disabled={!input.trim() || loading}
              className="rounded-xl bg-paddy hover:bg-paddy-deep flex-shrink-0"
              aria-label="Gửi"
            >
              <Send className="w-5 h-5" />
            </Button>
          </div>
          </>
          )}
        </div>
      </div>
    </section>
  );
}
