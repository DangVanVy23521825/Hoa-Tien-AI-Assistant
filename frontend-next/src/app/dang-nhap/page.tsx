"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AlertCircle } from "lucide-react";

export default function DangNhapPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [registerName, setRegisterName] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.login(loginEmail, loginPassword);
      login(res.access_token, res.user);
      router.push("/tro-ly");
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 0
          ? "Không kết nối được máy chủ."
          : err instanceof ApiError
          ? err.message
          : "Đã có lỗi xảy ra"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.register(registerEmail, registerPassword, registerName);
      login(res.access_token, res.user);
      router.push("/tro-ly");
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 0
          ? "Không kết nối được máy chủ."
          : err instanceof ApiError
          ? err.message
          : "Đã có lỗi xảy ra"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="max-w-md mx-auto px-6 py-14">
      <div className="bg-white border border-line rounded-2xl shadow-lg overflow-hidden">
        <div className="px-7 pt-6 pb-4 border-b border-line">
          <div className="text-[11px] font-bold tracking-wider uppercase text-river">
            Tài khoản
          </div>
          <h1 className="text-xl font-bold mt-1.5">Chào bạn</h1>
        </div>

        <div className="p-7">
          <Tabs defaultValue="login" className="w-full">
            <TabsList className="w-full bg-[#f1f4ef] p-1 rounded-xl mb-5">
              <TabsTrigger
                value="login"
                className="flex-1 rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm"
              >
                Đăng nhập
              </TabsTrigger>
              <TabsTrigger
                value="register"
                className="flex-1 rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm"
              >
                Đăng ký
              </TabsTrigger>
            </TabsList>

            {error && (
              <div className="mb-4 bg-[#fdf0ee] border border-[#f3d4cf] text-[#b3413c] text-sm px-3 py-2.5 rounded-lg flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {error}
              </div>
            )}

            <TabsContent value="login">
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <Label htmlFor="loginEmail" className="text-sm font-semibold text-ink-soft">
                    Email
                  </Label>
                  <Input
                    id="loginEmail"
                    type="email"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    required
                    autoComplete="email"
                    className="mt-1.5 border-line focus:border-paddy focus:ring-paddy/10"
                  />
                </div>
                <div>
                  <Label htmlFor="loginPassword" className="text-sm font-semibold text-ink-soft">
                    Mật khẩu
                  </Label>
                  <Input
                    id="loginPassword"
                    type="password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                    className="mt-1.5 border-line focus:border-paddy focus:ring-paddy/10"
                  />
                </div>
                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-paddy hover:bg-paddy-deep mt-2"
                >
                  {loading ? "Đang xử lý..." : "Đăng nhập"}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="register">
              <form onSubmit={handleRegister} className="space-y-4">
                <div>
                  <Label htmlFor="registerName" className="text-sm font-semibold text-ink-soft">
                    Họ tên hiển thị
                  </Label>
                  <Input
                    id="registerName"
                    type="text"
                    value={registerName}
                    onChange={(e) => setRegisterName(e.target.value)}
                    required
                    className="mt-1.5 border-line focus:border-paddy focus:ring-paddy/10"
                  />
                </div>
                <div>
                  <Label htmlFor="registerEmail" className="text-sm font-semibold text-ink-soft">
                    Email
                  </Label>
                  <Input
                    id="registerEmail"
                    type="email"
                    value={registerEmail}
                    onChange={(e) => setRegisterEmail(e.target.value)}
                    required
                    autoComplete="email"
                    className="mt-1.5 border-line focus:border-paddy focus:ring-paddy/10"
                  />
                </div>
                <div>
                  <Label htmlFor="registerPassword" className="text-sm font-semibold text-ink-soft">
                    Mật khẩu (tối thiểu 6 ký tự)
                  </Label>
                  <Input
                    id="registerPassword"
                    type="password"
                    value={registerPassword}
                    onChange={(e) => setRegisterPassword(e.target.value)}
                    required
                    minLength={6}
                    autoComplete="new-password"
                    className="mt-1.5 border-line focus:border-paddy focus:ring-paddy/10"
                  />
                </div>
                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-paddy hover:bg-paddy-deep mt-2"
                >
                  {loading ? "Đang xử lý..." : "Tạo tài khoản"}
                </Button>
              </form>
            </TabsContent>
          </Tabs>

          <p className="text-xs text-ink-soft mt-5 text-center">
            Bạn không cần đăng nhập để hỏi trợ lý hay tra cứu thủ tục — đăng
            nhập chỉ để lưu lại lịch sử câu hỏi của bạn.
          </p>
        </div>
      </div>
    </section>
  );
}
