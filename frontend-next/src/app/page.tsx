import Link from "next/link";
import Image from "next/image";
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
  Landmark,
  BookText,
  ArrowRight,
  Phone,
} from "lucide-react";

/* Văn phong hành chính, trang trọng nhưng vẫn dễ hiểu — cố ý tránh giọng
   quảng cáo sản phẩm, vì đây là trợ lý của chính quyền xã.

   KHÔNG nêu "trình tự thực hiện": chuỗi "trình tự" không xuất hiện một lần nào
   trong knowledge base và không thủ tục nào có trường quy trình các bước (cùng
   lý do đã loại mục "Quy trình" khỏi trang chi tiết thủ tục). Nêu ra là hứa thứ
   hệ thống không có. Thay bằng "căn cứ pháp lý" — trường legalBasis có thật ở
   cả 19 thủ tục. */
const CAPABILITIES = [
  {
    icon: Search,
    title: "Tra cứu thủ tục hành chính",
    body: "Hỗ trợ tra cứu thông tin thủ tục hành chính bằng ngôn ngữ tự nhiên, bao gồm tên thủ tục, thành phần hồ sơ, căn cứ pháp lý và các điều kiện có liên quan.",
  },
  {
    icon: ClipboardList,
    title: "Hướng dẫn chuẩn bị và thực hiện hồ sơ",
    body: "Cung cấp thông tin về thành phần hồ sơ, lệ phí, thời hạn giải quyết, cơ quan thực hiện và hình thức nộp hồ sơ. Nội dung hướng dẫn có thể được tổng hợp thành checklist để thuận tiện cho việc chuẩn bị và thực hiện.",
  },
  {
    icon: Landmark,
    title: "Tra cứu thông tin về địa phương",
    body: "Cung cấp thông tin về lịch sử hình thành, di tích, lễ hội, làng nghề, văn hóa và 15 thôn thuộc xã Hòa Tiến, góp phần hỗ trợ người dân tìm hiểu về lịch sử, văn hóa và đời sống địa phương.",
  },
  {
    icon: BookText,
    title: "Cung cấp nguồn thông tin đối chiếu",
    body: "Các câu trả lời được cung cấp kèm theo nguồn dữ liệu và căn cứ liên quan để người dân thuận tiện kiểm tra, đối chiếu. Trường hợp hệ thống không có đủ thông tin làm căn cứ trả lời, AI sẽ thông báo rõ và không tự suy đoán.",
  },
];

/* Câu mẫu lấy từ knowledge base thật + thống kê câu người dân hỏi nhiều nhất.
   Không đưa câu mà xã không giải quyết (ví dụ cấp CCCD — việc của Công an xã):
   người xem bấm thử sẽ nhận đúng câu "ngoài phạm vi", phản tác dụng khi trình diễn.

   Cơ cấu cố ý: 3 hành chính + 2 lịch sử + 1 văn hóa, để người xem thấy ngay trợ lý
   không chỉ biết thủ tục. Cả 6 câu đã chạy qua scripts/eval_retrieval.py trên KB
   hiện tại, câu thấp nhất 11.40 điểm (ngưỡng MIN_MATCH_SCORE = 4.0) — THÊM/SỬA câu
   nào thì phải đo lại, chip bấm ra fallback trước ban giám khảo là hỏng buổi demo. */
const SAMPLE_QUESTIONS = [
  "Đăng ký khai sinh cho con cần giấy tờ gì?",
  "Chứng thực bản sao từ bản chính mất bao nhiêu tiền?",
  "Bộ phận Một cửa làm việc mấy giờ?",
  "Xã Hòa Tiến được hình thành từ khi nào?",
  "Di tích Chiến thắng Gò Hà có ý nghĩa gì?",
  "Làng nghề dệt chiếu Cẩm Nê có gì đặc biệt?",
];

export default function HomePage() {
  return (
    <>
      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 pt-14 pb-12 sm:pb-24 md:pt-18 overflow-x-clip">
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
              Hiểu Hòa Tiến, chỉ bằng{" "}
              <em className="font-serif italic font-semibold text-paddy">
                một câu hỏi
              </em>
              .
            </h1>
            <p className="mt-5 text-lg text-ink-soft max-w-md">
              Trợ lý AI dành cho người dân xã Hòa Tiến — hỏi từ thủ tục hành
              chính đến lịch sử, văn hóa, làng nghề của xã. Chỉ trả lời trong
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

          {/* Mascot nhô ra sau khung chat — như đang đứng giới thiệu trợ lý.
              Ẩn dưới sm để không chen chỗ trên điện thoại. */}
          <div className="relative">
            <DemoChat />
            <Image
              src="/mascot/mascot.png"
              alt="Mascot cú Hòa Tiến AI"
              width={288}
              height={288}
              priority
              className="hidden sm:block absolute -bottom-24 -left-6 w-28 h-auto drop-shadow-xl pointer-events-none select-none"
            />
          </div>
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

      {/* ── AI hỗ trợ người dân những gì? ────────────────────── */}
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
            AI hỗ trợ người dân những gì?
          </h2>
        </div>
        {/* 2 cột thay vì 4: văn phong hành chính dài gấp mấy lần bản cũ,
            nhồi 4 cột thì mỗi thẻ thành một cột chữ hẹp và cao. */}
        <div className="grid sm:grid-cols-2 gap-4">
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

      {/* ── Cơ sở để AI cung cấp thông tin đáng tin cậy ───────── */}
      <section className="bg-gradient-to-b from-white/75 to-[#f7f3e8]/75 border-t border-b border-line py-14 px-6">
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
              Cơ sở để AI cung cấp thông tin đáng tin cậy
            </h2>
            <p className="mt-2 text-ink-soft max-w-2xl mx-auto">
              Trợ lý AI sử dụng nguồn dữ liệu được quản lý và cung cấp cho hệ
              thống, thay vì trả lời dựa trên thông tin chung không được kiểm
              chứng trên Internet. Mỗi yêu cầu được xử lý qua bốn bước nhằm bảo
              đảm câu trả lời có căn cứ và phù hợp với phạm vi thông tin của địa
              phương.
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
            {/* Trang /lien-he đã bỏ — thông tin liên hệ nằm ở footer, nên nút
                này gọi thẳng Bộ phận Một cửa thay vì điều hướng thêm một bước. */}
            <a href="tel:02363846176">
              <Button
                size="lg"
                variant="outline"
                className="border-white/35 bg-transparent text-white hover:bg-white/10 hover:text-white gap-2"
              >
                <Phone className="w-4 h-4" />
                Gọi UBND xã
              </Button>
            </a>
          </div>
        </div>
      </section>
    </>
  );
}
