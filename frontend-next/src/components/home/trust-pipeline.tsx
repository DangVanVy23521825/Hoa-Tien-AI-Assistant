import { Database, Search, Sparkles, Quote, ArrowDown } from "lucide-react";

/* "Cơ sở để AI cung cấp thông tin đáng tin cậy" — kể đúng luồng RAG thật
   (retrieve() hybrid trên pgvector -> Gemini bị ép grounding -> trích nguồn),
   không phải sơ đồ trang trí. Mô tả từng bước phải khớp rules/ai-module.md. */

const STEPS = [
  {
    icon: Database,
    title: "Cơ sở dữ liệu của xã",
    caption: "Knowledge Base",
    body: "Hệ thống sử dụng dữ liệu về thủ tục hành chính, thông tin địa phương, nội dung hỏi đáp và thông tin liên hệ do UBND xã Hòa Tiến cung cấp và quản lý.",
  },
  {
    icon: Search,
    title: "Xác định thông tin liên quan",
    caption: "Retrieval",
    body: "Hệ thống phân tích yêu cầu và tìm kiếm các nội dung phù hợp trong cơ sở dữ liệu bằng phương pháp kết hợp giữa tìm kiếm từ khóa và tìm kiếm ngữ nghĩa. Các yêu cầu nằm ngoài phạm vi dữ liệu được kiểm soát và xử lý theo quy định của hệ thống.",
  },
  {
    icon: Sparkles,
    title: "Tổng hợp và diễn giải thông tin",
    caption: "AI reasoning",
    body: "AI tổng hợp và diễn giải thông tin từ các dữ liệu đã được truy xuất, nhằm cung cấp câu trả lời rõ ràng, dễ hiểu và phù hợp với nhu cầu của người sử dụng. AI không tự bổ sung thông tin khi không có đủ căn cứ.",
  },
  {
    icon: Quote,
    title: "Cung cấp nguồn đối chiếu",
    caption: "Citation",
    body: "Câu trả lời được kèm theo thông tin về nguồn dữ liệu và căn cứ liên quan, giúp người dân thuận tiện kiểm tra và đối chiếu. Trường hợp không có đủ căn cứ, hệ thống sẽ thông báo rõ thay vì đưa ra thông tin không xác thực.",
  },
];

export default function TrustPipeline() {
  return (
    <ol className="max-w-3xl mx-auto space-y-0">
      {STEPS.map((s, i) => (
        <li key={s.title}>
          <div className="flex gap-4 bg-white border border-line rounded-2xl p-5">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-paddy to-river text-white grid place-items-center flex-shrink-0">
              <s.icon className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <div className="text-[11px] font-semibold uppercase tracking-widest text-river">
                {String(i + 1).padStart(2, "0")} — {s.caption}
              </div>
              <h3 className="font-semibold text-[15px] mt-0.5">{s.title}</h3>
              <p className="text-sm text-ink-soft mt-1">{s.body}</p>
            </div>
          </div>
          {i < STEPS.length - 1 && (
            <div className="grid place-items-center py-2" aria-hidden="true">
              <ArrowDown className="w-4 h-4 text-line" />
            </div>
          )}
        </li>
      ))}
    </ol>
  );
}
