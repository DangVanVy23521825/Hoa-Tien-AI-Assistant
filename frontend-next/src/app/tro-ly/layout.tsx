import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Trợ lý AI",
  description: "Hỏi Trợ lý AI xã Hòa Tiến bằng tiếng Việt tự nhiên: thủ tục hành chính, thông tin liên hệ, lịch sử — văn hóa — làng nghề của xã, trả lời kèm dẫn nguồn.",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
