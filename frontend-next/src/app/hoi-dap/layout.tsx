import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Hỏi đáp",
  description: "Câu hỏi thường gặp về giờ làm việc, nộp hồ sơ trực tuyến và thông tin xã Hòa Tiến.",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
