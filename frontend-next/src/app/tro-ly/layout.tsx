import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Trợ lý AI",
  description: "Hỏi thủ tục hành chính xã Hòa Tiến bằng tiếng Việt tự nhiên — trả lời kèm dẫn nguồn, hồ sơ cần chuẩn bị và mã QR nộp trực tuyến.",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
