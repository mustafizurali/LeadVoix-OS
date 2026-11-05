"use client";

import { useEffect, useState } from "react";
import { UserCheck, Mail, Building, Phone, AlertCircle } from "lucide-react";

import DashboardLayout from "@/modules/dashboard/components/DashboardLayout";
import {
  DemoRequest,
  getDemoRequests,
  updateDemoRequestStatus,
} from "@/modules/demo-requests/api/demoRequestApi";
import {
  PageContainer,
  PageHeader,
  EmptyState,
} from "@/components/crm";

const statuses = [
  "new",
  "contacted",
  "qualified",
  "converted",
  "closed",
];

export default function DemoRequestsPage() {
  const [requests, setRequests] = useState<DemoRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadRequests = async () => {
    try {
      setError("");
      const data = await getDemoRequests();
      setRequests(data);
    } catch (err) {
      console.error("Failed to load demo requests:", err);
      setError("Failed to load inbound demo requests.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRequests();
  }, []);

  const handleStatusChange = async (id: number, newStatus: string) => {
    try {
      const updatedRequest = await updateDemoRequestStatus(id, newStatus);
      setRequests((currentRequests) =>
        currentRequests.map((request) =>
          request.id === id ? updatedRequest : request
        )
      );
    } catch (err) {
      console.error("Failed to update demo request status:", err);
      setError("Failed to update request status.");
    }
  };

  return (
    <DashboardLayout>
      <PageContainer>
        <PageHeader
          title="Demo Requests"
          subtitle="Inbound enterprise consultation requests submitted via marketing and landing pages."
          badge="Inbound Pipeline"
        />

        {error && (
          <div className="flex items-center gap-2.5 rounded-xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-400">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {loading ? (
          <div className="rounded-xl border border-[#273449] bg-[#151D32] p-8 text-center text-sm text-[#94A3B8]">
            Loading demo requests...
          </div>
        ) : requests.length === 0 ? (
          <EmptyState
            title="No demo requests received"
            description="Inbound demo submissions from website visitors will appear here."
            icon={UserCheck}
          />
        ) : (
          <div className="overflow-hidden rounded-xl border border-[#273449] bg-[#151D32] shadow-sm">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-[#273449] text-left text-sm">
                <thead className="bg-[#0E1528] text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">
                  <tr>
                    <th className="px-6 py-3.5">Prospect</th>
                    <th className="px-6 py-3.5">Email</th>
                    <th className="px-6 py-3.5">Company</th>
                    <th className="px-6 py-3.5">Phone</th>
                    <th className="px-6 py-3.5">Message</th>
                    <th className="px-6 py-3.5">Status</th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-[#273449]">
                  {requests.map((request) => (
                    <tr
                      key={request.id}
                      className="transition hover:bg-[#1E293B]/40"
                    >
                      <td className="px-6 py-4 font-medium text-[#F5F7FC]">
                        {request.name}
                      </td>

                      <td className="px-6 py-4 font-mono text-xs text-[#94A3B8]">
                        <span className="flex items-center gap-1.5">
                          <Mail className="h-3 w-3 text-[#7657F6]" />
                          {request.email}
                        </span>
                      </td>

                      <td className="px-6 py-4 text-xs text-[#F5F7FC]">
                        <span className="flex items-center gap-1.5">
                          <Building className="h-3 w-3 text-[#24C8D8]" />
                          {request.company}
                        </span>
                      </td>

                      <td className="px-6 py-4 font-mono text-xs text-[#94A3B8]">
                        {request.phone ? (
                          <span className="flex items-center gap-1.5">
                            <Phone className="h-3 w-3 text-[#94A3B8]" />
                            {request.phone}
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>

                      <td className="max-w-xs truncate px-6 py-4 text-xs text-[#94A3B8]">
                        {request.message || "—"}
                      </td>

                      <td className="px-6 py-4">
                        <select
                          value={request.status}
                          onChange={(event) =>
                            handleStatusChange(request.id, event.target.value)
                          }
                          className="rounded-lg border border-[#273449] bg-[#0E1528] px-2.5 py-1 text-xs font-medium text-[#F5F7FC] outline-none transition focus:border-[#7657F6]"
                        >
                          {statuses.map((status) => (
                            <option key={status} value={status}>
                              {status.charAt(0).toUpperCase() + status.slice(1)}
                            </option>
                          ))}
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </PageContainer>
    </DashboardLayout>
  );
}
