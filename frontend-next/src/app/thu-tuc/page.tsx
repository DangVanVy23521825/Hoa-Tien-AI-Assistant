"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api, Procedure } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Clock, DollarSign, ArrowRight } from "lucide-react";

export default function ThuTucPage() {
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getProcedures()
      .then(setProcedures)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="max-w-6xl mx-auto px-6 py-14">
      <div className="mb-8">
        <Badge
          variant="secondary"
          className="mb-3 bg-river-deep/8 text-river-deep font-semibold tracking-wider uppercase text-xs px-3 py-1.5 rounded-full"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-paddy mr-2" />
          Dịch vụ công
        </Badge>
        <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight">
          Danh mục thủ tục hành chính
        </h2>
        <p className="mt-2 text-ink-soft max-w-xl">
          Nhấn vào từng thủ tục để xem hồ sơ cần chuẩn bị, lệ phí, thời gian xử
          lý và mã QR nộp trực tuyến.
        </p>
      </div>

      {loading ? (
        <div className="text-center py-12 text-ink-soft">Đang tải...</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {procedures.map((p) => (
            <Link key={p.code} href={`/thu-tuc/${p.code}`}>
              <Card className="group relative cursor-pointer hover:shadow-lg hover:-translate-y-1 hover:border-[#d3ead9] transition-all h-full">
                <CardHeader className="pb-3">
                  <div className="text-[11px] font-semibold tracking-wider uppercase text-river mb-2">
                    {p.category}
                  </div>
                  <CardTitle className="text-lg">{p.name}</CardTitle>
                  <CardDescription className="text-ink-soft">
                    {p.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-3.5 text-xs text-ink-soft">
                    <span className="flex items-center gap-1">
                      <DollarSign className="w-3.5 h-3.5 text-paddy-deep" />
                      <span className="font-semibold text-paddy-deep">
                        Phí:
                      </span>{" "}
                      {p.fee.split("(")[0]}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-paddy-deep" />
                      {p.processing_time}
                    </span>
                  </div>
                </CardContent>
                <div className="absolute top-5 right-5 text-line group-hover:text-paddy transition-colors">
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
