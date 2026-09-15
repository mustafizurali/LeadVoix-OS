import api from "@/lib/api/axios";

export type DemoRequest = {
  id: number;
  name: string;
  email: string;
  company: string;
  phone: string | null;
  message: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export const getDemoRequests = async (): Promise<DemoRequest[]> => {
  const response = await api.get("/demo-requests/");
  return response.data;
};

export const updateDemoRequestStatus = async (
  id: number,
  newStatus: string
): Promise<DemoRequest> => {
  const response = await api.put(
    `/demo-requests/${id}/status`,
    null,
    {
      params: {
        new_status: newStatus,
      },
    }
  );

  return response.data;
};