import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Thủ tục hành chính",
  description: "Danh mục thủ tục hành chính xã Hòa Tiến: hồ sơ cần chuẩn bị, lệ phí, thời gian xử lý và mã QR nộp trực tuyến.",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
