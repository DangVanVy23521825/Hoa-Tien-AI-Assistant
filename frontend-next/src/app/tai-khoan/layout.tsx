import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Tài khoản",
  description:
    "Thông tin tài khoản của bạn trên Trợ lý AI xã Hòa Tiến: họ tên, email, số câu đã hỏi và số phản ánh đã gửi.",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
