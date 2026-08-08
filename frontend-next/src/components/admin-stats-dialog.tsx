"use client";

import { useEffect, useState } from "react";
import { api, AdminStats } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export default function AdminStatsDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    api
      .getAdminStats()
      .then((s) => {
        if (cancelled) return;
        setStats(s);
        setError(false);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [open]);

  const tiles = stats
    ? [
        { label: "Tổng lượt hỏi", value: stats.total },
        { label: "Khớp dữ liệu", value: stats.matched },
        { label: "Chưa có dữ liệu", value: stats.unmatched },
        { label: "Chào hỏi, xã giao", value: stats.smalltalk ?? 0 },
        { label: "Đánh giá hữu ích", value: `${stats.helpful} 👍 / ${stats.unhelpful} 👎` },
      ]
    : [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>📊 Thống kê sử dụng</DialogTitle>
          <DialogDescription>
            Số liệu tổng hợp từ lượt hỏi của người dân, dùng để bổ sung dữ liệu
            còn thiếu.
          </DialogDescription>
        </DialogHeader>

        {error && (
          <p className="text-sm text-destructive">Không tải được thống kê.</p>
        )}
        {!stats && !error && (
          <p className="text-sm text-muted-foreground">Đang tải...</p>
        )}

        {stats && (
          <div className="space-y-5">
            <div className="grid grid-cols-2 gap-2.5">
              {tiles.map((t) => (
                <div
                  key={t.label}
                  className="bg-muted border border-line rounded-xl px-4 py-3"
                >
                  <div className="text-xs text-ink-soft">{t.label}</div>
                  <div className="text-lg font-bold text-paddy-deep">
                    {t.value}
                  </div>
                </div>
              ))}
            </div>

            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-paddy-deep mb-2">
                Thủ tục được hỏi nhiều nhất
              </h4>
              {stats.top_procedures.length === 0 ? (
                <p className="text-sm text-ink-soft">Chưa có dữ liệu.</p>
              ) : (
                <ul className="space-y-1.5">
                  {stats.top_procedures.map((p) => (
                    <li
                      key={p.name}
                      className="flex justify-between gap-3 text-sm border-b border-dashed border-line pb-1.5 last:border-0"
                    >
                      <span>{p.name}</span>
                      <span className="font-semibold text-paddy-deep">
                        {p.count}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-paddy-deep mb-2">
                Câu hỏi chưa có dữ liệu trả lời
              </h4>
              {stats.recent_unmatched.length === 0 ? (
                <p className="text-sm text-ink-soft">Chưa có câu nào.</p>
              ) : (
                <ul className="space-y-1.5">
                  {stats.recent_unmatched.map((q, i) => (
                    <li
                      key={i}
                      className="text-sm border-b border-dashed border-line pb-1.5 last:border-0"
                    >
                      <div>{q.question}</div>
                      <div className="text-xs text-ink-soft">
                        {new Date(q.created_at).toLocaleString("vi-VN")}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
