"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import {
  User,
  getStoredUser,
  setSession as apiSetSession,
  clearSession as apiClearSession,
} from "@/lib/api";

interface AuthContextType {
  user: User | null;
  setUser: (user: User | null) => void;
  login: (token: string, user: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  setUser: () => {},
  login: () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // Đọc localStorage trong useEffect, không trong initializer của useState:
  // HTML prerender luôn ở trạng thái chưa đăng nhập, nếu render đầu ở client
  // đã có user thì React báo hydration mismatch.
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    // Cascading render 1 lần khi mount là chủ đích: đây là cách duy nhất đọc
    // localStorage mà không lệch với HTML đã prerender.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setUser(getStoredUser());
  }, []);

  const login = useCallback((token: string, user: User) => {
    apiSetSession(token, user);
    setUser(user);
  }, []);

  const logout = useCallback(() => {
    apiClearSession();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, setUser, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
