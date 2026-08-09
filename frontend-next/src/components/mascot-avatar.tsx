import Image from "next/image";
import { cn } from "@/lib/utils";

/**
 * Avatar mặt mascot cho bong bóng tin nhắn của trợ lý.
 * Dùng chung giữa /tro-ly và khung demo ở trang chủ để hai nơi không lệch nhau.
 */
export default function MascotAvatar({
  size = 28,
  className,
}: {
  size?: number;
  className?: string;
}) {
  return (
    <Image
      src="/mascot/mascot-face.png"
      alt="Trợ lý Hòa Tiến AI"
      width={size}
      height={size}
      /* style thay vì class: bong bóng tin nhắn là flex align-stretch,
         thiếu chiều cao tường minh thì ảnh bị kéo giãn theo chiều cao hàng. */
      style={{ width: size, height: size }}
      className={cn(
        "self-start rounded-lg bg-white ring-1 ring-line object-cover flex-shrink-0",
        className,
      )}
    />
  );
}
