"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AlertCircle, MailCheck } from "lucide-react";

const RESEND_COOLDOWN = 60;

function errorMessage(err: unknown) {
  if (err instanceof ApiError) {
    return err.status === 0 ? "Không kết nối được máy chủ." : err.message;
  }
  return "Đã có lỗi xảy ra";
}

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

  // Bước xác thực OTP: vào từ đăng ký, hoặc từ đăng nhập bằng tài khoản chưa xác thực.
  const [otpEmail, setOtpEmail] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [cooldown]);

  const goToOtpStep = useCallback((email: string) => {
    setOtpEmail(email);
    setOtpCode("");
    setCooldown(RESEND_COOLDOWN);
  }, []);

  const handleLogin = async (e: React.SubmitEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.login(loginEmail, loginPassword);
      login(res.access_token, res.user);
      router.push("/tro-ly");
    } catch (err) {
      // Tài khoản đăng ký dở chưa xác thực: đưa thẳng vào màn nhập mã, gửi lại mã luôn
      // thay vì bắt người dùng tự mò sang tab đăng ký.
      if (err instanceof ApiError && err.code === "email_unverified") {
        goToOtpStep(loginEmail);
        try {
          await api.resendOtp(loginEmail);
        } catch {
          // Có thể vướng cooldown vì mã cũ vừa gửi — mã cũ vẫn dùng được.
        }
      } else {
        setError(errorMessage(err));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.SubmitEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.register(registerEmail, registerPassword, registerName);
      goToOtpStep(registerEmail);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e: React.SubmitEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.verifyOtp(otpEmail, otpCode);
      login(res.access_token, res.user);
      router.push("/tro-ly");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError("");
    setLoading(true);
    try {
      await api.resendOtp(otpEmail);
      setCooldown(RESEND_COOLDOWN);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const errorBanner = error && (
    <div className="mb-4 bg-[#fdf0ee] border border-[#f3d4cf] text-[#b3413c] text-sm px-3 py-2.5 rounded-lg flex items-center gap-2">
      <AlertCircle className="w-4 h-4 flex-shrink-0" />
      {error}
    </div>
  );

  if (otpEmail) {
    return (
      <section className="max-w-md mx-auto px-6 py-14">
        <div className="bg-white border border-line rounded-2xl shadow-lg overflow-hidden">
          <div className="px-7 pt-6 pb-4 border-b border-line">
            <div className="text-[11px] font-bold tracking-wider uppercase text-river">
              Xác thực email
            </div>
            <h1 className="text-xl font-bold mt-1.5">Nhập mã gồm 6 chữ số</h1>
          </div>

          <div className="p-7">
            <div className="mb-5 flex items-start gap-2.5 text-sm text-ink-soft">
              <MailCheck className="w-4.5 h-4.5 flex-shrink-0 mt-0.5 text-paddy" />
              <p>
                Chúng tôi đã gửi mã xác thực tới <b className="text-ink">{otpEmail}</b>. Mã có
                hiệu lực trong 10 phút. Nếu không thấy, hãy kiểm tra cả hộp thư rác.
              </p>
            </div>

            {errorBanner}

            <form onSubmit={handleVerify} className="space-y-4">
              <div>
                <Label htmlFor="otpCode" className="text-sm font-semibold text-ink-soft">
                  Mã xác thực
                </Label>
                <Input
                  id="otpCode"
                  type="text"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  required
                  autoFocus
                  placeholder="000000"
                  className="mt-1.5 border-line focus:border-paddy focus:ring-paddy/10 text-center text-2xl font-bold tracking-[0.4em]"
                />
              </div>
              <Button
                type="submit"
                disabled={loading || otpCode.length !== 6}
                className="w-full bg-paddy hover:bg-paddy-deep mt-2"
              >
                {loading ? "Đang xác thực..." : "Xác thực và vào trợ lý"}
              </Button>
            </form>

            <div className="mt-5 flex items-center justify-between text-sm">
              <button
                type="button"
                onClick={handleResend}
                disabled={loading || cooldown > 0}
                className="text-paddy font-semibold disabled:text-ink-soft disabled:font-normal"
              >
                {cooldown > 0 ? `Gửi lại mã sau ${cooldown}s` : "Gửi lại mã"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setOtpEmail("");
                  setError("");
                }}
                className="text-ink-soft hover:text-ink"
              >
                Đổi email
              </button>
            </div>
          </div>
        </div>
      </section>
    );
  }

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

            {errorBanner}

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
                  <p className="text-xs text-ink-soft mt-1.5">
                    Chúng tôi sẽ gửi mã xác thực 6 số tới email này.
                  </p>
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
            Bạn được hỏi thử trợ lý vài câu mà không cần tài khoản. Đăng ký để hỏi
            không giới hạn và lưu lại lịch sử câu hỏi của mình.
          </p>
        </div>
      </div>
    </section>
  );
}
