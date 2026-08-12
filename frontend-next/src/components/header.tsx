"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import AdminStatsDialog from "@/components/admin-stats-dialog";
import { Menu, User, LogOut, BarChart3, Info } from "lucide-react";

const navLinks = [
  { href: "/tro-ly", label: "Trợ lý AI" },
  { href: "/thu-tuc", label: "Thủ tục" },
  { href: "/hoi-dap", label: "Hỏi đáp" },
];

export default function Header() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [statsOpen, setStatsOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-line">
      <div className="relative bg-cream/92 backdrop-blur-md overflow-hidden">
        {/* Ảnh quê hương chiếm nửa phải header. Lớp kem phủ dày ở mép trái rồi
            loãng dần sang phải, cộng quầng sáng ở chỗ nối, để ảnh "loang" ra từ
            tên ứng dụng thay vì cắt khối. Ẩn dưới sm: điện thoại chỉ đủ chỗ cho
            tên app + nút. */}
        <div
          aria-hidden="true"
          className="hidden sm:block absolute inset-y-0 right-0 w-[64%] pointer-events-none select-none"
        >
          <Image
            src="/header/hoa-tien-band.jpg"
            alt=""
            fill
            priority
            sizes="64vw"
            className="object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-cream via-cream/45 to-cream/10" />
          {/* Mép trái: vừa mờ vừa chói, tan dần vào nền kem. */}
          <div className="absolute inset-y-0 left-0 w-48 backdrop-blur-[6px] [mask-image:linear-gradient(to_right,black_10%,transparent)]" />
          <div className="absolute inset-y-0 -left-20 w-64 bg-[radial-gradient(ellipse_at_left,rgba(255,255,255,0.9),transparent_72%)] blur-lg" />
        </div>

        <div className="relative max-w-7xl mx-auto px-6 py-5 flex items-center gap-3.5">
        <Link href="/" className="flex items-center gap-3 no-underline">
          <Image
            src="/mascot/mascot-face.png"
            alt="Mascot Hòa Tiến AI"
            width={40}
            height={40}
            priority
            className="w-10 h-10 rounded-xl bg-white ring-1 ring-line object-cover shadow-sm"
          />
          <div>
            <div className="font-semibold text-base tracking-tight text-ink">
              Hòa Tiến AI
            </div>
            {/* Ẩn dưới sm: chỗ hẹp thì dòng này xuống hàng, header cao vống lên. */}
            <div className="hidden sm:block text-[11px] text-ink-soft tracking-widest uppercase whitespace-nowrap">
              Trợ lý hành chính số
            </div>
          </div>
        </Link>

        {/* Nav nằm đè lên ảnh nên phải có nền kem mờ riêng, không thì chữ ink
            chìm vào mái nhà/ruộng sáng trong ảnh. */}
        <nav className="ml-auto hidden md:flex items-center gap-1.5 bg-cream/70 backdrop-blur-sm rounded-2xl p-1 ring-1 ring-white/50">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`text-sm font-medium px-3.5 py-2 rounded-lg transition-colors ${
                pathname === link.href
                  ? "bg-white text-paddy-deep shadow-sm"
                  : "text-ink-soft hover:bg-white hover:text-paddy-deep"
              }`}
            >
              {link.label}
            </Link>
          ))}
          <Link
            href="/tro-ly"
            className="ml-1.5 bg-paddy text-white font-semibold px-3.5 py-2 rounded-lg hover:bg-paddy-deep transition-colors"
          >
            Hỏi ngay
          </Link>
        </nav>

        <div className="ml-auto md:ml-4">
          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger
                render={
                  <Button
                    variant="outline"
                    className="gap-2 border-line bg-cream/80 backdrop-blur-sm hover:border-paddy"
                  />
                }
              >
                <span className="w-5 h-5 rounded-full bg-paddy text-white grid place-items-center text-[11px] font-bold">
                  {user.display_name.charAt(0).toUpperCase()}
                </span>
                <span className="hidden sm:inline">
                  {user.display_name.split(" ")[0]}
                </span>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-52">
                <DropdownMenuLabel>
                  <div className="font-medium">{user.display_name}</div>
                  <div className="text-xs text-muted-foreground">
                    {user.email}
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                {user.role === "admin" && (
                  <DropdownMenuItem onClick={() => setStatsOpen(true)}>
                    <BarChart3 className="w-4 h-4 mr-2" />
                    Thống kê
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem onClick={logout}>
                  <LogOut className="w-4 h-4 mr-2" />
                  Đăng xuất
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Link href="/dang-nhap">
              <Button
                variant="outline"
                className="gap-2 border-line bg-cream/80 backdrop-blur-sm hover:border-paddy"
              >
                <User className="w-4 h-4" />
                Đăng nhập
              </Button>
            </Link>
          )}
        </div>

        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetTrigger
            render={
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden ml-2"
                aria-label="Menu"
              />
            }
          >
            <Menu className="w-5 h-5" />
          </SheetTrigger>
          <SheetContent side="right" className="w-64">
            <nav className="flex flex-col gap-2 mt-8">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className={`px-4 py-3 rounded-lg font-medium transition-colors ${
                    pathname === link.href
                      ? "bg-paddy/10 text-paddy-deep"
                      : "text-ink-soft hover:bg-muted"
                  }`}
                >
                  {link.label}
                </Link>
              ))}
              <Link
                href="/tro-ly"
                onClick={() => setMobileOpen(false)}
                className="mt-2 bg-paddy text-white font-semibold px-4 py-3 rounded-lg text-center hover:bg-paddy-deep"
              >
                Hỏi ngay
              </Link>
            </nav>
          </SheetContent>
        </Sheet>
        </div>
      </div>

      {/* Thông báo phạm vi sử dụng — trước ở footer, đưa lên đây để giám khảo và
          người dân đọc được ngay trước khi hỏi, không phải cuộn xuống cuối trang. */}
      <div className="bg-paddy-deep text-white/85 text-[11px] sm:text-xs">
        <div className="max-w-7xl mx-auto px-6 py-1.5 flex items-start gap-2">
          <Info className="w-3.5 h-3.5 mt-px shrink-0 text-rice" />
          <p className="leading-snug">
            <span className="font-semibold text-white">
              Hệ thống thử nghiệm phục vụ dự thi &ldquo;Ý tưởng sáng tạo · Hòa
              Tiến số&rdquo; của thôn Phú Sơn Nam.
            </span>{" "}
            <span className="hidden sm:inline">
              Dữ liệu thủ tục mang tính tham khảo, cần đối soát với UBND xã Hòa
              Tiến trước khi sử dụng chính thức.
            </span>
          </p>
        </div>
      </div>

      {user?.role === "admin" && (
        <AdminStatsDialog open={statsOpen} onOpenChange={setStatsOpen} />
      )}
    </header>
  );
}
