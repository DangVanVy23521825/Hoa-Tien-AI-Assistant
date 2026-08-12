"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { api, Procedure } from "@/lib/api";
import { categoryFacets, filterProcedures } from "@/lib/procedure-filter";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Clock,
  DollarSign,
  ArrowRight,
  Search,
  MessageSquare,
  X,
} from "lucide-react";

export default function ThuTucPage() {
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<string | null>(null);

  useEffect(() => {
    api
      .getProcedures()
      .then(setProcedures)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const facets = useMemo(() => categoryFacets(procedures), [procedures]);
  const visible = useMemo(
    () => filterProcedures(procedures, { query, category }),
    [procedures, query, category],
  );

  const trimmed = query.trim();
  const isFiltering = trimmed !== "" || category !== null;
  const clearFilters = () => {
    setQuery("");
    setCategory(null);
  };

  const chipBase =
    "shrink-0 inline-flex items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors cursor-pointer";
  const chipOn = "bg-paddy text-white border-paddy";
  const chipOff =
    "bg-white text-ink-soft border-line hover:border-paddy hover:text-paddy-deep";

  return (
    <section className="max-w-6xl mx-auto px-6 py-14">
      <div className="mb-6">
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

      <div className="relative mb-4">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-soft pointer-events-none" />
        <Input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Tìm thủ tục"
          placeholder="Tìm thủ tục: khai sinh, tạm trú, sổ đỏ…"
          className="h-11 pl-10 pr-4 rounded-xl border-line bg-white text-[15px]"
        />
      </div>

      <div
        className="flex gap-2 overflow-x-auto pb-2 mb-4 -mx-1 px-1"
        role="group"
        aria-label="Lọc theo lĩnh vực"
      >
        <button
          type="button"
          onClick={() => setCategory(null)}
          aria-pressed={category === null}
          className={`${chipBase} ${category === null ? chipOn : chipOff}`}
        >
          Tất cả
          <span className="opacity-70">{procedures.length}</span>
        </button>
        {facets.map((f) => (
          <button
            key={f.category}
            type="button"
            onClick={() => setCategory(f.category)}
            aria-pressed={category === f.category}
            className={`${chipBase} ${category === f.category ? chipOn : chipOff}`}
          >
            <span aria-hidden="true">{f.icon}</span>
            {f.category}
            <span className="opacity-70">{f.count}</span>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-12 text-ink-soft">Đang tải...</div>
      ) : (
        <>
          <div className="flex items-center gap-3 mb-4 text-sm text-ink-soft">
            <span aria-live="polite">
              Hiển thị {visible.length} / {procedures.length} thủ tục
            </span>
            {isFiltering && (
              <button
                type="button"
                onClick={clearFilters}
                className="inline-flex items-center gap-1 text-paddy-deep font-medium hover:underline cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
                Xoá bộ lọc
              </button>
            )}
          </div>

          {visible.length === 0 ? (
            <div className="border border-line rounded-2xl bg-cream px-6 py-10 text-center">
              <p className="font-semibold mb-2">
                {trimmed
                  ? `Không tìm thấy thủ tục nào khớp “${trimmed}”`
                  : "Không có thủ tục nào trong lĩnh vực này"}
              </p>
              <p className="text-sm text-ink-soft max-w-md mx-auto mb-6">
                Trợ lý AI tra cứu rộng hơn danh mục này — kho dữ liệu của xã có
                225 bản ghi, gồm cả lịch sử, văn hoá và làng nghề.
              </p>
              <div className="flex flex-wrap gap-3 justify-center">
                {trimmed && (
                  <Link href={`/tro-ly?q=${encodeURIComponent(trimmed)}`}>
                    <Button className="bg-paddy hover:bg-paddy-deep gap-2">
                      <MessageSquare className="w-4 h-4" />
                      Hỏi trợ lý: “{trimmed}”
                    </Button>
                  </Link>
                )}
                <Button
                  variant="outline"
                  onClick={clearFilters}
                  className="border-line hover:border-paddy hover:text-paddy-deep gap-2"
                >
                  <X className="w-4 h-4" />
                  Xoá bộ lọc
                </Button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {visible.map((p) => (
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
        </>
      )}
    </section>
  );
}
