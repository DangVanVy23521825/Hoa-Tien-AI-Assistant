import Image from "next/image";

/**
 * Ảnh drone quê hương Hòa Tiến làm nền cố định cho toàn site.
 *
 * Nằm sau mọi nội dung (-z-10) và phủ lớp kem 92% nên không đụng tới độ tương
 * phản chữ. `scale-105` bù phần mép bị blur ăn vào, tránh lộ viền trong suốt.
 */
export default function SiteBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none" aria-hidden="true">
      <Image
        src="/bg/hoa-tien.jpg"
        alt=""
        fill
        priority
        sizes="100vw"
        className="object-cover scale-105 blur-[3px]"
      />
      <div className="absolute inset-0 bg-cream/92" />
    </div>
  );
}
