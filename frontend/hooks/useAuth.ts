"use client";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useUserStore } from "@/store/userStore";
import { TokenResponse, User } from "@/types/user";
import toast from "react-hot-toast";

interface LoginCredentials {
  email: string;
  password: string;
}

interface RegisterData {
  username: string;
  email: string;
  password: string;
}

async function resolveAuthUser(data: TokenResponse): Promise<User> {
  if (data.user) return data.user;
  const me = await api.get<User>("/api/v1/auth/me");
  return me.data;
}

export function useLogin() {
  const router = useRouter();
  const { setUser, setTokens } = useUserStore();

  return useMutation({
    mutationFn: async (credentials: LoginCredentials) => {
      const res = await api.post<TokenResponse>("/api/v1/auth/login", credentials);
      return res.data;
    },
    onSuccess: async (data) => {
      if (!data.access_token || !data.refresh_token) {
        toast.error("Login response is incomplete. Please try again.");
        return;
      }
      setTokens(data.access_token, data.refresh_token);
      const user = await resolveAuthUser(data);
      setUser(user);
      toast.success(`Welcome back, ${user.username}!`);
      router.push("/dashboard");
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        "Invalid credentials";
      toast.error(message);
    },
  });
}

export function useLogout() {
  const router = useRouter();
  const { clearUser } = useUserStore();

  return useMutation({
    mutationFn: async () => {
      try {
        await api.post("/api/v1/auth/logout");
      } catch {
        // Ignore logout errors
      }
    },
    onSettled: () => {
      clearUser();
      router.push("/login");
    },
  });
}

export function useRegister() {
  const router = useRouter();
  const { setUser, setTokens } = useUserStore();

  return useMutation({
    mutationFn: async (data: RegisterData) => {
      const res = await api.post<TokenResponse>("/api/v1/auth/register", data);
      return res.data;
    },
    onSuccess: async (data) => {
      if (data.requires_email_verification) {
        const email = data.user?.email || "";
        const msg =
          data.message ||
          "Account created. Please verify your email before signing in.";
        toast.success(msg);
        const target = email
          ? `/login?verify=pending&email=${encodeURIComponent(email)}`
          : "/login?verify=pending";
        router.push(target);
        return;
      }

      if (!data.access_token || !data.refresh_token) {
        toast.error("Registration completed but token response is missing.");
        return;
      }

      setTokens(data.access_token, data.refresh_token);
      const user = await resolveAuthUser(data);
      setUser(user);
      toast.success("Account created successfully!");
      router.push("/dashboard");
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        "Registration failed. Please try again.";
      toast.error(message);
    },
  });
}
