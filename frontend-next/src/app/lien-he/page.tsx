"use client";

import { useState, useEffect } from "react";
import { api, Contact, qr } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { MapPin, Phone, Clock, Globe } from "lucide-react";

export default function LienHePage() {
  const [contact, setContact] = useState<Contact | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getContacts()
      .then(setContact)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-14 text-center text-ink-soft">
        Đang tải...
      </div>
    );
  }

  if (!contact) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-14 text-center text-ink-soft">
        Không tải được thông tin liên hệ.
      </div>
    );
  }

  const rows = [
    { icon: MapPin, label: "Địa chỉ", value: contact.address },
    { icon: Phone, label: "Điện thoại", value: contact.phone },
    { icon: Clock, label: "Giờ làm việc", value: contact.working_hours.weekdays },
    { icon: Globe, label: "Cổng thông tin", value: contact.portal_url },
  ];

  return (
    <section className="bg-gradient-to-br from-paddy-deep to-river-deep text-white py-14 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <Badge
            variant="secondary"
            className="mb-3 bg-white/14 text-white font-semibold tracking-wider uppercase text-xs px-3 py-1.5 rounded-full"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-rice mr-2" />
            Liên hệ
          </Badge>
          <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white">
            Ủy ban nhân dân xã Hòa Tiến
          </h2>
          <p className="mt-2 text-white/85 max-w-xl">
            Nếu trợ lý chưa trả lời được, hãy liên hệ trực tiếp bộ phận Một cửa
            của xã.
          </p>
        </div>

        <div className="grid md:grid-cols-[1.3fr_0.7fr] gap-7">
          <div className="space-y-3.5">
            {rows.map((row, i) => (
              <div
                key={i}
                className="flex gap-3.5 items-start bg-white/8 border border-white/14 rounded-xl px-5 py-4"
              >
                <div className="w-10 h-10 rounded-xl bg-white/14 grid place-items-center flex-shrink-0">
                  <row.icon className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wider opacity-75 mb-0.5">
                    {row.label}
                  </div>
                  <div className="text-[15px]">{row.value}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-white rounded-2xl p-6 text-center text-ink">
            <img
              src={qr(contact.portal_url, 150)}
              alt="QR cổng thông tin xã"
              className="w-[150px] h-[150px] mx-auto"
            />
            <div className="mt-3 font-semibold text-sm">
              Cổng thông tin xã Hòa Tiến
            </div>
            <small className="text-xs text-ink-soft">
              Quét để truy cập nhanh
            </small>
          </div>
        </div>
      </div>
    </section>
  );
}
