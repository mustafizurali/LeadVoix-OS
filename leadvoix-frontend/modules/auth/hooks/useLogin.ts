import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { login } from "../api/authApi";
import { useAuthStore } from "../store/authStore";

import { tokenStorage } from "@/lib/api/tokenStorage";

export const useLogin = () => {
  const router = useRouter();

  const setAccessToken = useAuthStore(
    (state) => state.setAccessToken
  );

  const setUser = useAuthStore(
    (state) => state.setUser
  );

  return useMutation({
    mutationFn: login,

    onSuccess: (data) => {
      tokenStorage.setToken(data.access_token);

      setAccessToken(data.access_token);

      try {
        const payload = JSON.parse(
          atob(data.access_token.split(".")[1])
        );

        setUser({
          id: payload.user_id,
          name: payload.sub,
          email: payload.sub,
          role: payload.role,
        });
      } catch (error) {
        console.error("Failed to decode access token", error);
      }

      router.replace("/dashboard");
    },

    onError: (error) => {
      console.error(error);
    },
  });
};