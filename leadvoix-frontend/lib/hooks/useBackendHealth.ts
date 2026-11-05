"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api/axios";

export function useBackendHealth() {
  return useQuery<boolean>({
    queryKey: ["backend-health"],
    queryFn: async () => {
      try {
        const response = await api.get("/");
        return response.status === 200;
      } catch {
        return false;
      }
    },
    staleTime: 30000,
    refetchInterval: 60000,
  });
}
