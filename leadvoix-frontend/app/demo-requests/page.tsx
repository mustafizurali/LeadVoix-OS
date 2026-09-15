"use client";

import { useEffect, useState } from "react";

import DashboardLayout from "@/modules/dashboard/components/DashboardLayout";
import {
  DemoRequest,
  getDemoRequests,
  updateDemoRequestStatus,
} from "@/modules/demo-requests/api/demoRequestApi";

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
      setError("Failed to load demo requests.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRequests();
  }, []);

  const handleStatusChange = async (
    id: number,
    newStatus: string
  ) => {
    try {
      const updatedRequest =
        await updateDemoRequestStatus(id, newStatus);

      setRequests((currentRequests) =>
        currentRequests.map((request) =>
          request.id === id
            ? updatedRequest
            : request
        )
      );
    } catch (err) {
      console.error(
        "Failed to update demo request status:",
        err
      );

      setError("Failed to update request status.");
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold">
            Demo Requests
          </h1>

          <p className="mt-2 text-slate-500">
            Manage demo requests submitted by potential clients.
          </p>
        </div>

        {loading ? (
          <div className="rounded-lg bg-white p-6 shadow-sm">
            Loading demo requests...
          </div>
        ) : error ? (
          <div className="rounded-lg bg-white p-6 shadow-sm">
            <p className="text-red-600">{error}</p>
          </div>
        ) : requests.length === 0 ? (
          <div className="rounded-lg bg-white p-6 shadow-sm">
            <p className="text-slate-600">
              No demo requests found.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg bg-white shadow-sm">
            <table className="w-full min-w-[900px]">
              <thead>
                <tr className="border-b border-slate-200 text-left">
                  <th className="px-6 py-4 text-sm font-semibold">
                    Name
                  </th>

                  <th className="px-6 py-4 text-sm font-semibold">
                    Email
                  </th>

                  <th className="px-6 py-4 text-sm font-semibold">
                    Company
                  </th>

                  <th className="px-6 py-4 text-sm font-semibold">
                    Phone
                  </th>

                  <th className="px-6 py-4 text-sm font-semibold">
                    Message
                  </th>

                  <th className="px-6 py-4 text-sm font-semibold">
                    Status
                  </th>
                </tr>
              </thead>

              <tbody>
                {requests.map((request) => (
                  <tr
                    key={request.id}
                    className="border-b border-slate-100 last:border-0"
                  >
                    <td className="px-6 py-4 font-medium">
                      {request.name}
                    </td>

                    <td className="px-6 py-4 text-sm text-slate-600">
                      {request.email}
                    </td>

                    <td className="px-6 py-4 text-sm text-slate-600">
                      {request.company}
                    </td>

                    <td className="px-6 py-4 text-sm text-slate-600">
                      {request.phone || "-"}
                    </td>

                    <td className="max-w-xs px-6 py-4 text-sm text-slate-600">
                      {request.message || "-"}
                    </td>

                    <td className="px-6 py-4">
                      <select
                        value={request.status}
                        onChange={(event) =>
                          handleStatusChange(
                            request.id,
                            event.target.value
                          )
                        }
                        className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                      >
                        {statuses.map((status) => (
                          <option
                            key={status}
                            value={status}
                          >
                            {status
                              .charAt(0)
                              .toUpperCase() +
                              status.slice(1)}
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}