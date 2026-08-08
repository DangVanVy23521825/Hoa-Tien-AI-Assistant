import { Database, Search, Sparkles, Quote, ArrowDown } from "lucide-react";

/* "Tại sao có thể tin tưởng?" — kể đúng luồng RAG thật của hệ thống
   (retrieve() hybrid trên pgvector -> Gemini bị ép grounding -> trích nguồn),
   không phải sơ đồ trang trí. Mô tả từng bước phải khớp rules/ai-module.md. */

const STEPS = [
  {
    icon: Database,
    title: "Dữ liệu của xã",
    caption: "Knowledge Base",
    body: "Thủ tục, hỏi đáp và thông tin liên hệ do UBND xã Hòa Tiến cung cấp — không lấy từ Internet.",
  },
  {
    icon: Search,
    title: "Tìm đúng mục liên quan",
    caption: "Retrieval",
    body: "Kết hợp khớp từ khoá và tìm kiếm ngữ nghĩa. Câu hỏi ngoài phạm vi bị chặn ngay ở bước này.",
  },
  {
    icon: Sparkles,
    title: "AI diễn giải dễ hiểu",
    caption: "AI reasoning",
    body: "AI chỉ được viết lại từ dữ liệu vừa tìm được. Không đủ căn cứ thì phải nói không biết.",
  },
  {
    icon: Quote,
    title: "Kèm nguồn để đối chiếu",
    caption: "Citation",
    body: "Mỗi câu trả lời đều dẫn tên mục dữ liệu và căn cứ pháp lý để người dân kiểm chứng.",
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
                {s.caption}
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
