"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, Procedure, qr } from "@/lib/api";
import { printChecklist } from "@/lib/print";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft,
  Printer,
  MessageSquare,
  FileText,
  Clock,
  DollarSign,
  MapPin,
  BookOpen,
} from "lucide-react";

export default function ThuTucDetailPage() {
  const params = useParams();
  const code = params.code as string;
  const [procedure, setProcedure] = useState<Procedure | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getProcedures()
      .then((procedures) => {
        const found = procedures.find((p) => p.code === code);
        setProcedure(found || null);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [code]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-14 text-center text-ink-soft">
        Đang tải...
      </div>
    );
  }

  if (!procedure) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-14 text-center">
        <h2 className="text-xl font-bold mb-4">Không tìm thấy thủ tục</h2>
        <Link href="/thu-tuc">
          <Button variant="outline">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Quay lại danh mục
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <section className="max-w-4xl mx-auto px-6 py-14">
      <Link
        href="/thu-tuc"
        className="inline-flex items-center gap-2 text-sm text-ink-soft hover:text-paddy-deep mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Quay lại danh mục
      </Link>

      <Badge
        variant="secondary"
        className="mb-3 bg-river-deep/8 text-river-deep font-semibold tracking-wider uppercase text-xs px-3 py-1.5 rounded-full"
      >
        {procedure.category}
      </Badge>
      <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight mb-4">
        {procedure.name}
      </h1>
      <p className="text-ink-soft mb-8">{procedure.description}</p>

      <div className="bg-white border border-line rounded-2xl p-6 mb-6">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-paddy-deep mb-4">
          Hồ sơ cần chuẩn bị
        </h3>
        <ul className="space-y-2">
          {procedure.documents.map((doc, i) => (
            <li
              key={i}
              className="flex items-start gap-2 text-[14.5px]"
            >
              <FileText className="w-4 h-4 text-paddy mt-0.5 flex-shrink-0" />
              {doc}
            </li>
          ))}
        </ul>
      </div>

      <div className="bg-white border border-line rounded-2xl p-6 mb-6">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-paddy-deep mb-4">
          Thông tin xử lý
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="bg-[#f4f7f2] border border-line rounded-xl px-4 py-3">
            <div className="text-xs font-semibold text-paddy-deep mb-1 flex items-center gap-1">
              <DollarSign className="w-3.5 h-3.5" />
              Lệ phí
            </div>
            <div className="text-sm">{procedure.fee}</div>
          </div>
          <div className="bg-[#f4f7f2] border border-line rounded-xl px-4 py-3">
            <div className="text-xs font-semibold text-paddy-deep mb-1 flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              Thời gian
            </div>
            <div className="text-sm">{procedure.processing_time}</div>
          </div>
          <div className="bg-[#f4f7f2] border border-line rounded-xl px-4 py-3">
            <div className="text-xs font-semibold text-paddy-deep mb-1 flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5" />
              Nơi nộp
            </div>
            <div className="text-sm">{procedure.place_of_submission}</div>
          </div>
          <div className="bg-[#f4f7f2] border border-line rounded-xl px-4 py-3">
            <div className="text-xs font-semibold text-paddy-deep mb-1 flex items-center gap-1">
              <BookOpen className="w-3.5 h-3.5" />
              Căn cứ
            </div>
            <div className="text-sm">{procedure.legal_basis}</div>
          </div>
        </div>
      </div>

      <div className="bg-cream border border-line rounded-2xl p-5 flex items-center gap-4 mb-6">
        <img
          src={qr(procedure.online_url, 96)}
          alt="QR nộp trực tuyến"
          className="w-24 h-24 rounded-lg"
        />
        <div>
          <div className="font-semibold">Nộp hồ sơ trực tuyến</div>
          <small className="text-xs text-ink-soft">
            Quét mã QR để đến Cổng Dịch vụ công Quốc gia và nộp hồ sơ{" "}
            {procedure.name.toLowerCase()}.
          </small>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <Button
          variant="outline"
          onClick={() => printChecklist(procedure)}
          className="border-line hover:border-paddy hover:text-paddy-deep gap-2"
        >
          <Printer className="w-4 h-4" />
          In checklist hồ sơ
        </Button>
        <Link href="/tro-ly">
          <Button className="bg-paddy hover:bg-paddy-deep gap-2">
            <MessageSquare className="w-4 h-4" />
            Hỏi trợ lý về thủ tục này
          </Button>
        </Link>
      </div>
    </section>
  );
}
