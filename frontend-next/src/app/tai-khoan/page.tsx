"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  UserRound,
  Mail,
  LogIn,
  LogOut,
  MessageSquare,
  Megaphone,
  ArrowRight,
} from "lucide-react";

/** Ô số liệu. `value === null` nghĩa là chưa đọc được — hiện "—" thay vì số 0 sai sự thật. */
function StatCard({
  href,
  icon,
  value,
  label,
  cta,
}: {
  href: string;
  icon: React.ReactNode;
  value: number | null;
  label: string;
  cta: string;
}) {
  return (
    <Link
      href={href}
      className="group flex flex-col rounded-2xl border border-line bg-white px-5 py-4 transition-all hover:-translate-y-0.5 hover:border-[#d3ead9] hover:shadow-lg"
    >
      <div className="mb-2 flex items-center gap-2 text-paddy-deep">
        {icon}
        <span className="text-xs font-semibold uppercase tracking-wider">
          {label}
        </span>
      </div>
      <div className="text-3xl font-extrabold tracking-tight">
        {value === null ? "—" : value}
      </div>
      <div className="mt-2 flex items-center gap-1 text-sm text-ink-soft group-hover:text-paddy-deep">
        {cta}
        <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
      </div>
    </Link>
  );
}

export default function TaiKhoanPage() {
  const { user, logout } = useAuth();
  const router = useRouter();

  // null = chưa đọc được (chưa xong hoặc lỗi mạng). Hai lời gọi chạy độc lập nhau,
  // một cái hỏng không được kéo cái kia xuống.
  const [chatCount, setChatCount] = useState<number | null>(null);
  const [reportCount, setReportCount] = useState<number | null>(null);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    api
      .getHistory()
      .then((h) => {
        if (!cancelled) setChatCount(h.length);
      })
      .catch(() => {});
    api
      .getMyReports()
      .then((r) => {
        if (!cancelled) setReportCount(r.length);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [user]);

  if (!user) {
    return (
      <section className="mx-auto max-w-3xl px-6 py-14">
        <div className="rounded-2xl border border-line bg-white px-6 py-10 text-center">
          <LogIn className="mx-auto mb-3 h-8 w-8 text-paddy" />
          <p className="mb-2 font-semibold">Bạn chưa đăng nhập</p>
          <p className="mx-auto mb-6 max-w-md text-sm text-ink-soft">
            Đăng nhập để xem thông tin tài khoản, lịch sử hỏi đáp và các phản ánh
            bạn đã gửi.
          </p>
          <Link href="/dang-nhap">
            <Button className="gap-2 bg-paddy hover:bg-paddy-deep">
              <LogIn className="h-4 w-4" />
              Đăng nhập / Đăng ký
            </Button>
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="mx-auto max-w-3xl px-6 py-14">
      <div className="mb-8">
        <Badge
          variant="secondary"
          className="mb-3 rounded-full bg-river-deep/8 px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-river-deep"
        >
          <span className="mr-2 h-1.5 w-1.5 rounded-full bg-paddy" />
          Tài khoản
        </Badge>
        <h2 className="text-2xl font-extrabold tracking-tight md:text-3xl">
          Thông tin tài khoản
        </h2>
      </div>

      <div className="mb-6 rounded-2xl border border-line bg-white p-6">
        <div className="flex items-center gap-4">
          <span className="grid h-14 w-14 shrink-0 place-items-center rounded-full bg-paddy text-xl font-bold text-white">
            {user.display_name.charAt(0).toUpperCase()}
          </span>
          <div className="min-w-0">
            <div className="truncate text-lg font-bold">
              {user.display_name}
            </div>
            <div className="mt-0.5 flex items-center gap-1.5 text-sm text-ink-soft">
              <Mail className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">{user.email}</span>
            </div>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-2 border-t border-line pt-5">
          <UserRound className="h-4 w-4 text-ink-soft" />
          <span className="text-sm text-ink-soft">Vai trò:</span>
          <Badge
            variant="secondary"
            className="rounded-full bg-paddy/10 px-3 py-1 text-xs font-semibold text-paddy-deep"
          >
            {user.role === "admin" ? "Quản trị viên" : "Người dân"}
          </Badge>
        </div>
      </div>

      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <StatCard
          href="/tro-ly"
          icon={<MessageSquare className="h-4 w-4" />}
          value={chatCount}
          label="Câu đã hỏi"
          cta="Mở trợ lý AI"
        />
        <StatCard
          href="/phan-anh"
          icon={<Megaphone className="h-4 w-4" />}
          value={reportCount}
          label="Phản ánh đã gửi"
          cta="Xem phản ánh của tôi"
        />
      </div>

      <Button
        variant="outline"
        onClick={() => {
          logout();
          router.push("/");
        }}
        className="gap-2 border-line hover:border-paddy hover:text-paddy-deep"
      >
        <LogOut className="h-4 w-4" />
        Đăng xuất
      </Button>
    </section>
  );
}
