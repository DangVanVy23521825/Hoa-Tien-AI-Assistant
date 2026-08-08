import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import ShareButton from "@/components/share-button";
import DemoChat from "@/components/home/demo-chat";
import TrustPipeline from "@/components/home/trust-pipeline";
import {
  MessageSquare,
  FileText,
  Search,
  ClipboardList,
  MapPin,
  BookText,
  ArrowRight,
} from "lucide-react";

const CAPABILITIES = [
  {
    icon: Search,
    title: "Tra cứu thủ tục",
    body: "Hỏi bằng tiếng Việt tự nhiên, kể cả khẩu ngữ — không cần biết tên gọi hành chính chính xác.",
  },
  {
    icon: ClipboardList,
    title: "Chuẩn bị hồ sơ",
    body: "Liệt kê đủ giấy tờ cần mang theo, lệ phí và thời gian xử lý. In được thành checklist.",
  },
  {
    icon: MapPin,
    title: "Tìm nơi thực hiện",
    body: "Chỉ đúng nơi nộp hồ sơ, giờ làm việc, số điện thoại — kèm mã QR nộp trực tuyến.",
  },
  {
    icon: BookText,
    title: "Dẫn nguồn",
    body: "Mọi câu trả lời đều kèm mục dữ liệu và căn cứ pháp lý để người dân đối chiếu.",
  },
];

/* Câu mẫu lấy từ knowledge base thật + thống kê câu người dân hỏi nhiều nhất.
   Không đưa câu mà xã không giải quyết (ví dụ cấp CCCD — việc của Công an xã):
   người xem bấm thử sẽ nhận đúng câu "ngoài phạm vi", phản tác dụng khi trình diễn. */
const SAMPLE_QUESTIONS = [
  "Đăng ký khai sinh cho con cần giấy tờ gì?",
  "Chứng thực bản sao từ bản chính mất bao nhiêu tiền?",
  "Đăng ký thường trú cần hồ sơ gì?",
  "Muốn chuyển nhượng đất thì làm thủ tục thế nào?",
  "Bộ phận Một cửa làm việc mấy giờ?",
  "Khai báo tạm vắng khi nào phải làm?",
];

export default function HomePage() {
  return (
    <>
      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 pt-14 pb-12 md:pt-18">
        <div className="grid md:grid-cols-[1.05fr_0.95fr] gap-10 md:gap-12 items-center">
          <div>
            <Badge
              variant="secondary"
              className="mb-5 bg-river-deep/8 text-river-deep font-semibold tracking-wider uppercase text-xs px-3 py-1.5 rounded-full"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-paddy mr-2" />
              Xã Hòa Tiến · TP Đà Nẵng
            </Badge>
            <h1 className="text-4xl md:text-5xl font-extrabold leading-tight tracking-tight text-ink">
              Hỏi một câu,{" "}
              <em className="font-serif italic font-semibold text-paddy">xong</em>{" "}
              thủ tục.
            </h1>
            <p className="mt-5 text-lg text-ink-soft max-w-md">
              Trợ lý hành chính AI dành cho người dân xã Hòa Tiến — trả lời trong
              phạm vi dữ liệu của xã và luôn kèm nguồn để đối chiếu.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link href="/tro-ly">
                <Button size="lg" className="bg-paddy hover:bg-paddy-deep gap-2">
                  <MessageSquare className="w-4 h-4" />
                  Bắt đầu hỏi
                </Button>
              </Link>
              <Link href="/thu-tuc">
                <Button
                  variant="outline"
                  size="lg"
                  className="border-line hover:border-paddy hover:text-paddy-deep gap-2"
                >
                  <FileText className="w-4 h-4" />
                  Xem thủ tục
                </Button>
              </Link>
              <ShareButton />
            </div>
            <div className="mt-8 flex flex-wrap gap-x-7 gap-y-3">
              {[
                { v: "24/7", l: "Hỏi được mọi lúc" },
                { v: "0 đ", l: "Miễn phí sử dụng" },
                { v: "Có dẫn nguồn", l: "Đối chiếu được" },
              ].map((s) => (
                <div key={s.v}>
                  <div className="text-2xl font-bold text-river-deep font-serif">
                    {s.v}
                  </div>
                  <div className="text-xs text-ink-soft">{s.l}</div>
                </div>
              ))}
            </div>
          </div>

          <DemoChat />
        </div>
      </section>

      <svg
        className="w-full h-4 text-rice opacity-80"
        viewBox="0 0 1200 18"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <path
          d="M0 9 Q30 0 60 9 T120 9 T180 9 T240 9 T300 9 T360 9 T420 9 T480 9 T540 9 T600 9 T660 9 T720 9 T780 9 T840 9 T900 9 T960 9 T1020 9 T1080 9 T1140 9 T1200 9"
          stroke="currentColor"
          strokeWidth="2"
          fill="none"
        />
      </svg>

      {/* ── AI giúp bạn làm gì? ──────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-14">
        <div className="mb-8">
          <Badge
            variant="secondary"
            className="mb-3 bg-river-deep/8 text-river-deep font-semibold tracking-wider uppercase text-xs px-3 py-1.5 rounded-full"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-paddy mr-2" />
            Khả năng
          </Badge>
          <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight">
            AI giúp bạn làm gì?
          </h2>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {CAPABILITIES.map((c) => (
            <div
              key={c.title}
              className="bg-white border border-line rounded-2xl p-5"
            >
              <div className="w-10 h-10 rounded-xl bg-paddy/10 text-paddy-deep grid place-items-center mb-3">
                <c.icon className="w-5 h-5" />
              </div>
              <h3 className="font-semibold">{c.title}</h3>
              <p className="text-sm text-ink-soft mt-1.5">{c.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Tại sao có thể tin tưởng? ────────────────────────── */}
      <section className="bg-gradient-to-b from-white to-[#f7f3e8] border-t border-b border-line py-14 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-8">
            <Badge
              variant="secondary"
              className="mb-3 bg-river-deep/8 text-river-deep font-semibold tracking-wider uppercase text-xs px-3 py-1.5 rounded-full"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-paddy mr-2" />
              Cách hoạt động
            </Badge>
            <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight">
              Tại sao có thể tin tưởng?
            </h2>
            <p className="mt-2 text-ink-soft max-w-xl mx-auto">
              Trợ lý không trả lời bằng kiến thức chung trên Internet. Mỗi câu đi
              qua bốn bước dưới đây — thiếu căn cứ thì từ chối, không suy đoán.
            </p>
          </div>
          <TrustPipeline />
        </div>
      </section>

      {/* ── Câu hỏi phổ biến ─────────────────────────────────── */}
      <section className="max-w-4xl mx-auto px-6 py-14">
        <div className="text-center mb-8">
          <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight">
            Một vài câu hỏi phổ biến
          </h2>
          <p className="mt-2 text-ink-soft">
            Bấm một câu để xem trợ lý trả lời ngay.
          </p>
        </div>
        <div className="flex flex-wrap justify-center gap-2.5">
          {SAMPLE_QUESTIONS.map((q) => (
            <Link
              key={q}
              href={`/tro-ly?q=${encodeURIComponent(q)}`}
              className="group bg-white border border-line rounded-full pl-4 pr-3 py-2.5 text-sm font-medium text-ink-soft hover:border-paddy hover:text-paddy-deep hover:bg-[#f6faf4] transition-colors inline-flex items-center gap-2"
            >
              {q}
              <ArrowRight className="w-3.5 h-3.5 opacity-50 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" />
            </Link>
          ))}
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────── */}
      <section className="px-6 pb-14">
        <div className="max-w-4xl mx-auto bg-gradient-to-br from-paddy-deep to-river-deep text-white rounded-3xl px-8 py-12 text-center">
          <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white">
            Không phải xếp hàng để hỏi một câu.
          </h2>
          <p className="mt-3 text-white/85 max-w-lg mx-auto">
            Hỏi trợ lý trước, biết cần mang theo giấy tờ gì, rồi mới ra Bộ phận
            Một cửa.
          </p>
          <div className="mt-7 flex flex-wrap justify-center gap-3">
            <Link href="/tro-ly">
              <Button
                size="lg"
                className="bg-white text-paddy-deep hover:bg-white/90 gap-2"
              >
                Hỏi trợ lý ngay
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
            <Link href="/lien-he">
              <Button
                size="lg"
                variant="outline"
                className="border-white/35 bg-transparent text-white hover:bg-white/10 hover:text-white"
              >
                Liên hệ UBND xã
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
