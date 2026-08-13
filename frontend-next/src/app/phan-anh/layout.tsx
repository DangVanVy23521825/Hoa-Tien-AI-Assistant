import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Phản ánh, kiến nghị",
  description:
    "Gửi phản ánh, kiến nghị về hạ tầng, môi trường, an ninh trật tự hay thủ tục hành chính trên địa bàn xã Hòa Tiến.",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
