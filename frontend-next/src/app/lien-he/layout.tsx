import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Liên hệ",
  description: "Địa chỉ, điện thoại, giờ làm việc của UBND xã Hòa Tiến và QR cổng thông tin xã.",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
