import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import ShareButton from "@/components/share-button";
import { MessageSquare, FileText } from "lucide-react";

export default function HomePage() {
  return (
    <>
      <section className="max-w-6xl mx-auto px-6 pt-16 pb-10 md:pt-20 md:pb-12">
        <div className="grid md:grid-cols-[1.1fr_0.9fr] gap-12 items-center">
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
              <em className="font-serif italic font-semibold text-paddy">
                xong
              </em>{" "}
              thủ tục.
            </h1>
            <p className="mt-5 text-lg text-ink-soft max-w-md">
              Trợ lý AI giúp người dân Hòa Tiến tra cứu thủ tục hành chính,
              biết cần chuẩn bị hồ sơ gì và liên hệ đúng nơi — bằng tiếng Việt,
              ngay trên điện thoại.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link href="/tro-ly">
                <Button size="lg" className="bg-paddy hover:bg-paddy-deep gap-2">
                  <MessageSquare className="w-4 h-4" />
                  Trò chuyện với trợ lý
                </Button>
              </Link>
              <Link href="/thu-tuc">
                <Button
                  variant="outline"
                  size="lg"
                  className="border-line hover:border-paddy hover:text-paddy-deep gap-2"
                >
                  <FileText className="w-4 h-4" />
                  Xem danh mục thủ tục
                </Button>
              </Link>
              <ShareButton />
            </div>
            <div className="mt-8 flex gap-7">
              <div>
                <div className="text-2xl font-bold text-river-deep font-serif">
                  24/7
                </div>
                <div className="text-xs text-ink-soft">Hỗ trợ mọi lúc</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-river-deep font-serif">
                  0 đ
                </div>
                <div className="text-xs text-ink-soft">Miễn phí sử dụng</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-river-deep font-serif">
                  Có dẫn nguồn
                </div>
                <div className="text-xs text-ink-soft">Thông tin đáng tin</div>
              </div>
            </div>
          </div>

          <div
            className="relative aspect-square rounded-3xl border border-line shadow-lg overflow-hidden hidden md:block"
            style={{
              background:
                "radial-gradient(circle at 30% 30%, rgba(232,184,75,0.18), transparent 40%), linear-gradient(160deg, #ffffff, #f3efe2)",
            }}
          >
            <svg
              viewBox="0 0 400 400"
              fill="none"
              className="absolute inset-0 w-full h-full"
            >
              <path
                d="M40 300 Q120 250 200 290 T380 270"
                stroke="#1d6f8b"
                strokeWidth="2.5"
                opacity=".35"
                fill="none"
              />
              <path
                d="M20 330 Q120 290 210 320 T390 300"
                stroke="#2f7d4f"
                strokeWidth="2.5"
                opacity=".3"
                fill="none"
              />
              <circle cx="120" cy="150" r="5" fill="#2f7d4f" />
              <circle cx="250" cy="200" r="5" fill="#1d6f8b" />
              <circle cx="180" cy="280" r="5" fill="#e8b84b" />
              <line
                x1="120"
                y1="150"
                x2="250"
                y2="200"
                stroke="#2f7d4f"
                strokeWidth="1.2"
                opacity=".3"
                strokeDasharray="4 4"
              />
              <line
                x1="250"
                y1="200"
                x2="180"
                y2="280"
                stroke="#1d6f8b"
                strokeWidth="1.2"
                opacity=".3"
                strokeDasharray="4 4"
              />
            </svg>
            <div className="absolute top-[16%] left-[10%] bg-white border border-line rounded-xl px-3 py-2 text-xs font-semibold shadow-lg flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-paddy" />
              UBND xã
            </div>
            <div className="absolute top-[44%] right-[8%] bg-white border border-line rounded-xl px-3 py-2 text-xs font-semibold shadow-lg flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-river" />
              Bộ phận Một cửa
            </div>
            <div className="absolute bottom-[14%] left-[22%] bg-white border border-line rounded-xl px-3 py-2 text-xs font-semibold shadow-lg flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-rice" />
              Dịch vụ công
            </div>
          </div>
        </div>
      </section>

      <svg
        className="w-full h-4 text-rice opacity-80"
        viewBox="0 0 1200 18"
        preserveAspectRatio="none"
      >
        <path
          d="M0 9 Q30 0 60 9 T120 9 T180 9 T240 9 T300 9 T360 9 T420 9 T480 9 T540 9 T600 9 T660 9 T720 9 T780 9 T840 9 T900 9 T960 9 T1020 9 T1080 9 T1140 9 T1200 9"
          stroke="currentColor"
          strokeWidth="2"
          fill="none"
        />
      </svg>
    </>
  );
}
