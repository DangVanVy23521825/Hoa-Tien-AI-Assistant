"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api, ApiError, Report, ReportCategory } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Megaphone,
  Send,
  MapPin,
  CheckCircle2,
  LogIn,
  AlertTriangle,
} from "lucide-react";

const CATEGORIES: { value: ReportCategory; label: string; icon: string }[] = [
  { value: "ha_tang", label: "Hạ tầng – giao thông", icon: "🛣️" },
  { value: "moi_truong", label: "Môi trường – vệ sinh", icon: "🌱" },
  { value: "an_ninh", label: "An ninh trật tự", icon: "🛡️" },
  { value: "thu_tuc", label: "Thủ tục hành chính", icon: "📄" },
  { value: "khac", label: "Khác", icon: "💬" },
];

const MIN_CONTENT = 20;
const MAX_CONTENT = 2000;

function categoryLabel(value: string): string {
  return CATEGORIES.find((c) => c.value === value)?.label ?? value;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

/** Ghi chú bắt buộc: nói thật phản ánh đi về đâu. Xem spec mục 5. */
function Disclaimer() {
  return (
    <div className="mt-6 flex gap-3 rounded-2xl border border-line bg-cream px-5 py-4 text-sm">
      <AlertTriangle className="w-5 h-5 text-paddy-deep shrink-0 mt-0.5" />
      <p className="text-ink-soft leading-relaxed">
        Phản ánh được gửi tới hòm thư của nhóm phát triển Trợ lý AI xã Hòa Tiến.
        Đây là sản phẩm dự thi,{" "}
        <b className="text-ink">không phải kênh tiếp nhận chính thức của UBND xã</b>.
        Việc khẩn cấp xin liên hệ trực tiếp UBND xã:{" "}
        <a href="tel:02363846176" className="font-semibold text-paddy-deep hover:underline">
          (0236) 3846176
        </a>
        .
      </p>
    </div>
  );
}

export default function PhanAnhPage() {
  const { user } = useAuth();

  const [category, setCategory] = useState<ReportCategory>("ha_tang");
  const [content, setContent] = useState("");
  const [location, setLocation] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [justSent, setJustSent] = useState<Report | null>(null);

  // `null` = chưa tải xong. Suy ra trạng thái tải thay vì giữ thêm một state riêng:
  // đặt state đồng bộ ngay trong effect sẽ gây render dây chuyền (eslint chặn).
  const [reports, setReports] = useState<Report[] | null>(null);
  const loadingList = user !== null && reports === null;

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    api
      .getMyReports()
      .then((r) => {
        if (!cancelled) setReports(r);
      })
      .catch(() => {
        // Không đọc được danh sách thì coi như rỗng — form vẫn gửi được bình thường.
        if (!cancelled) setReports([]);
      });
    return () => {
      cancelled = true;
    };
  }, [user]);

  const trimmed = content.trim();
  const canSend = trimmed.length >= MIN_CONTENT && !sending;

  const submit = async () => {
    if (!canSend) return;
    setSending(true);
    setError("");
    try {
      const report = await api.createReport({
        category,
        content: trimmed,
        location: location.trim() || undefined,
      });
      setJustSent(report);
      setContent("");
      setLocation("");
      setReports((prev) => [report, ...(prev ?? [])]);
    } catch (e) {
      setError(
        e instanceof ApiError ? e.message : "Không gửi được, vui lòng thử lại.",
      );
    } finally {
      setSending(false);
    }
  };

  return (
    <section className="max-w-3xl mx-auto px-6 py-14">
      <div className="mb-8">
        <Badge
          variant="secondary"
          className="mb-3 bg-river-deep/8 text-river-deep font-semibold tracking-wider uppercase text-xs px-3 py-1.5 rounded-full"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-paddy mr-2" />
          Tiếp nhận
        </Badge>
        <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight flex items-center gap-2.5">
          <Megaphone className="w-7 h-7 text-paddy" />
          Phản ánh, kiến nghị
        </h2>
        <p className="mt-2 text-ink-soft">
          Thấy cột điện nghiêng, cống tắc, rác tồn đọng hay có góp ý về thủ tục
          hành chính? Gửi cho chúng tôi để được ghi nhận.
        </p>
      </div>

      {!user ? (
        <>
          <div className="border border-line rounded-2xl bg-white px-6 py-10 text-center">
            <LogIn className="w-8 h-8 text-paddy mx-auto mb-3" />
            <p className="font-semibold mb-2">Cần đăng nhập để gửi phản ánh</p>
            <p className="text-sm text-ink-soft max-w-md mx-auto mb-6">
              Phản ánh gắn với một tài khoản đã xác thực email để cán bộ biết ai
              gửi và liên hệ lại khi cần làm rõ.
            </p>
            <Link href="/dang-nhap">
              <Button className="bg-paddy hover:bg-paddy-deep gap-2">
                <LogIn className="w-4 h-4" />
                Đăng nhập / Đăng ký
              </Button>
            </Link>
          </div>
          <Disclaimer />
        </>
      ) : (
        <>
          {justSent && (
            <div className="mb-6 rounded-2xl border border-[#bbf7d0] bg-[#f0fdf4] px-6 py-5 flex items-start gap-3">
              <CheckCircle2 className="w-6 h-6 text-paddy-deep shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-paddy-deep">
                  Đã ghi nhận phản ánh của bạn
                </p>
                <p className="text-sm text-ink-soft mt-1">
                  Mã phiếu của bạn là{" "}
                  <b className="text-ink text-base tracking-wide">
                    {justSent.code}
                  </b>{" "}
                  — hãy ghi lại để tiện nhắc tới khi liên hệ.
                </p>
              </div>
            </div>
          )}

          <div className="border border-line rounded-2xl bg-white p-6">
            <label className="block text-sm font-semibold mb-2.5">
              Lĩnh vực
            </label>
            <div className="flex flex-wrap gap-2 mb-6">
              {CATEGORIES.map((c) => (
                <button
                  key={c.value}
                  type="button"
                  onClick={() => setCategory(c.value)}
                  aria-pressed={category === c.value}
                  className={`inline-flex items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors cursor-pointer ${
                    category === c.value
                      ? "bg-paddy text-white border-paddy"
                      : "bg-white text-ink-soft border-line hover:border-paddy hover:text-paddy-deep"
                  }`}
                >
                  <span aria-hidden="true">{c.icon}</span>
                  {c.label}
                </button>
              ))}
            </div>

            <label
              htmlFor="report-content"
              className="block text-sm font-semibold mb-2.5"
            >
              Nội dung phản ánh
            </label>
            <textarea
              id="report-content"
              value={content}
              onChange={(e) => setContent(e.target.value.slice(0, MAX_CONTENT))}
              rows={6}
              placeholder="Mô tả càng cụ thể càng dễ xử lý: chuyện gì, ở đâu, từ bao giờ…"
              className="w-full rounded-xl border border-line bg-white px-4 py-3 text-[15px] leading-relaxed outline-none transition-colors focus-visible:border-paddy focus-visible:ring-3 focus-visible:ring-paddy/20"
            />
            <div className="mt-1.5 mb-5 flex justify-between text-xs text-ink-soft">
              <span>
                {trimmed.length < MIN_CONTENT
                  ? `Cần thêm ${MIN_CONTENT - trimmed.length} ký tự nữa`
                  : " "}
              </span>
              <span>
                {content.length}/{MAX_CONTENT}
              </span>
            </div>

            <label
              htmlFor="report-location"
              className="block text-sm font-semibold mb-2.5"
            >
              Địa điểm{" "}
              <span className="font-normal text-ink-soft">(không bắt buộc)</span>
            </label>
            <div className="relative mb-6">
              <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-soft pointer-events-none" />
              <Input
                id="report-location"
                value={location}
                onChange={(e) => setLocation(e.target.value.slice(0, 200))}
                placeholder="Ví dụ: thôn Nam Sơn, gần cầu…"
                className="h-11 pl-10 pr-4 rounded-xl border-line bg-white text-[15px]"
              />
            </div>

            {error && (
              <p className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </p>
            )}

            <Button
              onClick={submit}
              disabled={!canSend}
              className="bg-paddy hover:bg-paddy-deep gap-2 disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              {sending ? "Đang gửi…" : "Gửi phản ánh"}
            </Button>
          </div>

          <Disclaimer />

          <div className="mt-10">
            <h3 className="text-lg font-bold mb-4">Phản ánh của tôi</h3>
            {loadingList ? (
              <p className="text-sm text-ink-soft">Đang tải…</p>
            ) : !reports || reports.length === 0 ? (
              <p className="text-sm text-ink-soft">
                Bạn chưa gửi phản ánh nào.
              </p>
            ) : (
              <ul className="space-y-3">
                {(reports ?? []).map((r) => (
                  <li
                    key={r.id}
                    className="rounded-2xl border border-line bg-white px-5 py-4"
                  >
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mb-2 text-xs">
                      <span className="font-bold tracking-wide text-paddy-deep">
                        {r.code}
                      </span>
                      <span className="text-river font-semibold uppercase tracking-wider">
                        {categoryLabel(r.category)}
                      </span>
                      <span className="text-ink-soft ml-auto">
                        {formatDate(r.created_at)}
                      </span>
                    </div>
                    <p className="text-[14.5px] whitespace-pre-wrap leading-relaxed">
                      {r.content}
                    </p>
                    {r.location && (
                      <p className="mt-2 text-xs text-ink-soft flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5" />
                        {r.location}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </section>
  );
}
