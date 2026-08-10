"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { api, Contact, qr } from "@/lib/api";
import { MapPin, Phone, Clock, Globe } from "lucide-react";

/**
 * Giá trị mặc định lấy từ data/seed-knowledge-base.json — cùng nguồn với API.
 * Có sẵn để footer vẫn hiện đủ thông tin liên hệ khi backend chưa/không phản hồi:
 * đây là thứ người dân cần nhất lúc hệ thống trục trặc.
 */
const FALLBACK: Contact = {
  address: "Thôn Phú Sơn Tây (Quốc lộ 14B), xã Hòa Tiến, TP Đà Nẵng",
  phone: "(0236) 3846176",
  working_hours: {
    weekdays: "Thứ 2 – Thứ 6: Sáng 07:30–11:30, Chiều 13:30–17:00",
    saturday:
      "Sáng thứ 7 làm việc theo lịch niêm yết (Trung tâm Phục vụ hành chính công cấp xã)",
  },
  portal_url: "https://hoatien.danang.gov.vn",
};

export default function Footer() {
  const [contact, setContact] = useState<Contact>(FALLBACK);

  useEffect(() => {
    api
      .getContacts()
      .then(setContact)
      .catch(() => {});
  }, []);

  const rows = [
    { icon: MapPin, label: "Địa chỉ", value: contact.address },
    { icon: Phone, label: "Điện thoại", value: contact.phone },
    {
      icon: Clock,
      label: "Giờ làm việc",
      value: contact.working_hours.saturday
        ? `${contact.working_hours.weekdays}. ${contact.working_hours.saturday}`
        : contact.working_hours.weekdays,
    },
  ];

  return (
    <footer className="bg-ink text-[#c8d0c9] text-sm">
      <div className="max-w-7xl mx-auto px-6 py-10 grid gap-8 md:grid-cols-[1.1fr_1.4fr_auto]">
        <div>
          <div className="flex items-center gap-3">
            <Image
              src="/mascot/mascot-face.png"
              alt="Mascot Hòa Tiến AI"
              width={36}
              height={36}
              style={{ width: 36, height: 36 }}
              className="rounded-xl bg-white/95 object-cover"
            />
            <div>
              <div className="text-white font-semibold">Hòa Tiến AI</div>
              <div className="text-[11px] uppercase tracking-widest opacity-70">
                Trợ lý hành chính số
              </div>
            </div>
          </div>
          <p className="mt-4 opacity-75 leading-relaxed">
            Trợ lý chỉ trả lời trong phạm vi dữ liệu của xã. Khi cần xác nhận
            chính thức, hãy liên hệ trực tiếp Bộ phận Một cửa.
          </p>
        </div>

        <div>
          <h2 className="text-white font-semibold mb-3">
            Ủy ban nhân dân xã Hòa Tiến
          </h2>
          <ul className="space-y-2.5">
            {rows.map((row) => (
              <li key={row.label} className="flex gap-2.5">
                <row.icon className="w-4 h-4 mt-0.5 shrink-0 text-rice" />
                <span className="leading-relaxed">
                  {row.label === "Điện thoại" ? (
                    <a
                      href={`tel:${row.value.replace(/[^\d+]/g, "")}`}
                      className="hover:text-white underline-offset-2 hover:underline"
                    >
                      {row.value}
                    </a>
                  ) : (
                    row.value
                  )}
                </span>
              </li>
            ))}
            <li className="flex gap-2.5">
              <Globe className="w-4 h-4 mt-0.5 shrink-0 text-rice" />
              <a
                href={contact.portal_url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-white underline-offset-2 hover:underline break-all"
              >
                {contact.portal_url}
              </a>
            </li>
          </ul>
        </div>

        <div className="text-center">
          {/* eslint-disable-next-line @next/next/no-img-element -- QR sinh từ API ngoài, không qua next/image */}
          <img
            src={qr(contact.portal_url, 108)}
            alt="QR cổng thông tin xã Hòa Tiến"
            className="w-[108px] h-[108px] mx-auto rounded-lg bg-white p-1.5"
          />
          <div className="mt-2 text-xs opacity-75">Quét vào cổng thông tin</div>
        </div>
      </div>

      <div className="border-t border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4 text-xs opacity-65 text-center">
          Sản phẩm dự thi &ldquo;Ý tưởng sáng tạo · Hòa Tiến số&rdquo; — hệ thống
          thử nghiệm, dữ liệu thủ tục cần đối soát với UBND xã trước khi sử dụng
          chính thức.
        </div>
      </div>
    </footer>
  );
}
