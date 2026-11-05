import { create } from "zustand";
import { tokenStorage, decodeJwtPayload } from "@/lib/api/tokenStorage";
import { AuthState, User } from "../types/auth.types";

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  isHydrated: false,

  setUser: (user: User) => {
    tokenStorage.setUser(user);
    set({
      user,
      isAuthenticated: !!get().accessToken,
    });
  },

  setAccessToken: (token: string) => {
    tokenStorage.setToken(token);
    set({
      accessToken: token,
      isAuthenticated: !!token,
    });
  },

  login: (user: User, token: string) => {
    tokenStorage.setToken(token);
    tokenStorage.setUser(user);
    set({
      user,
      accessToken: token,
      isAuthenticated: true,
      isHydrated: true,
    });
  },

  logout: () => {
    tokenStorage.clear();
    set({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isHydrated: true,
    });
  },

  hydrate: () => {
    if (typeof window === "undefined") return;

    const token = tokenStorage.getToken();
    if (!token) {
      set({
        user: null,
        accessToken: null,
        isAuthenticated: false,
        isHydrated: true,
      });
      return;
    }

    const payload = decodeJwtPayload(token);
    // Check if token has expired
    if (
      payload &&
      typeof payload.exp === "number" &&
      Date.now() >= payload.exp * 1000
    ) {
      tokenStorage.clear();
      set({
        user: null,
        accessToken: null,
        isAuthenticated: false,
        isHydrated: true,
      });
      return;
    }

    let user = tokenStorage.getUser();
    if (!user && payload && payload.sub && payload.user_id) {
      user = {
        id: Number(payload.user_id),
        email: String(payload.sub),
        name: undefined,
        role: String(payload.role || "user"),
      };
      tokenStorage.setUser(user);
    }

    set({
      user,
      accessToken: token,
      isAuthenticated: !!token,
      isHydrated: true,
    });
  },
}));

// Hydrate store immediately in the browser
if (typeof window !== "undefined") {
  useAuthStore.getState().hydrate();
}
