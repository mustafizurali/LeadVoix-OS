"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";

import { login as loginApi } from "../api/authApi";
import { useAuthStore } from "../store/authStore";
import { decodeJwtPayload, getSafeRedirectUrl } from "@/lib/api/tokenStorage";
import { LoginRequest, User } from "../types/auth.types";

export const useLogin = () => {
  const router = useRouter();
  const searchParams = useSearchParams();

  const loginAction = useAuthStore((state) => state.login);

  return useMutation({
    mutationFn: (data: LoginRequest) => loginApi(data),

    onSuccess: (data, variables) => {
      const payload = decodeJwtPayload(data.access_token);

      const user: User = {
        id: payload?.user_id ? Number(payload.user_id) : 0,
        email: payload?.sub ? String(payload.sub) : variables.email,
        name: undefined, // Backend JWT currently omits real name; display fallback will use email
        role: payload?.role ? String(payload.role) : "user",
      };

      loginAction(user, data.access_token);

      const redirectParam = searchParams?.get("redirect");
      const target = getSafeRedirectUrl(redirectParam, "/dashboard");
      router.replace(target);
    },
  });
};
