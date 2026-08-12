import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Đăng nhập",
  description: "Đăng nhập hoặc tạo tài khoản để lưu lịch sử hỏi đáp với Trợ lý AI xã Hòa Tiến.",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
