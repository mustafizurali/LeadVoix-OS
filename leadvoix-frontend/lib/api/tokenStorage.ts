const ACCESS_TOKEN_KEY = "leadvoix_access_token";
const USER_KEY = "leadvoix_user";

export interface StoredUser {
  id: number;
  name?: string;
  email: string;
  role: string;
  organization_id?: number;
  organization_name?: string;
}

export function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split(".");
    if (parts.length < 2) return null;
    let base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    while (base64.length % 4 !== 0) {
      base64 += "=";
    }
    const jsonStr = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(jsonStr);
  } catch {
    return null;
  }
}

export function getSafeRedirectUrl(
  target: string | null | undefined,
  defaultUrl = "/dashboard"
): string {
  if (!target || typeof target !== "string") return defaultUrl;
  const trimmed = target.trim();
  if (
    !trimmed.startsWith("/") ||
    trimmed.startsWith("//") ||
    trimmed.startsWith("/\\")
  ) {
    return defaultUrl;
  }
  if (
    trimmed === "/login" ||
    trimmed.startsWith("/login?") ||
    trimmed === "/signup" ||
    trimmed.startsWith("/signup?")
  ) {
    return defaultUrl;
  }
  return trimmed;
}

export const tokenStorage = {
  getToken: (): string | null => {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },

  setToken: (token: string) => {
    if (typeof window === "undefined") return;
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
  },

  removeToken: () => {
    if (typeof window === "undefined") return;
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },

  getUser: (): StoredUser | null => {
    if (typeof window === "undefined") return null;
    try {
      const data = localStorage.getItem(USER_KEY);
      if (!data) return null;
      return JSON.parse(data) as StoredUser;
    } catch {
      localStorage.removeItem(USER_KEY);
      return null;
    }
  },

  setUser: (user: StoredUser) => {
    if (typeof window === "undefined") return;
    try {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    } catch {
      // Storage quota or serialization issue
    }
  },

  removeUser: () => {
    if (typeof window === "undefined") return;
    localStorage.removeItem(USER_KEY);
  },

  clear: () => {
    if (typeof window === "undefined") return;
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};
