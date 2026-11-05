"use client";

import { useEffect, useState } from "react";
import { Bot, ChevronDown } from "lucide-react";

import DashboardLayout from "@/modules/dashboard/components/DashboardLayout";
import AgentCallList from "@/modules/agent-calls/components/AgentCallList";
import api from "@/lib/api/axios";
import { PageContainer, PageHeader, EmptyState, StatusBadge } from "@/components/crm";

type Agent = {
  id: number;
  name: string;
  is_active: boolean;
};

export default function AgentCallsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAgents = async () => {
      try {
        const response = await api.get("/agents");
        const agentList: Agent[] = response.data;
        setAgents(agentList);

        if (agentList.length > 0) {
          setSelectedAgentId(agentList[0].id);
        }
      } catch (error) {
        console.error("Failed to load agents:", error);
      } finally {
        setLoading(false);
      }
    };

    loadAgents();
  }, []);

  const selectedAgent = agents.find((a) => a.id === selectedAgentId);

  return (
    <DashboardLayout>
      <PageContainer>
        <PageHeader
          title="Telephony & Agent Calls"
          subtitle="Review live conversational call sessions, audio recordings, and automated deal intelligence."
          badge="Autonomous Voice"
        />

        {loading ? (
          <div className="rounded-xl border border-[#273449] bg-[#151D32] p-8 text-center text-sm text-[#94A3B8]">
            Loading voice agents...
          </div>
        ) : agents.length === 0 ? (
          <EmptyState
            title="No AI Voice Agents found"
            description="Create an AI Voice Agent first to initiate outbound calls and inspect conversational intelligence."
            icon={Bot}
          />
        ) : (
          <div className="space-y-6">
            {/* AGENT SELECTOR BAR */}
            <div className="flex flex-col gap-3 rounded-xl border border-[#273449] bg-[#151D32] p-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#24C8D8]/10 border border-[#24C8D8]/20 text-[#24C8D8]">
                  <Bot className="h-5 w-5" />
                </div>
                <div>
                  <label
                    htmlFor="agent-select"
                    className="block text-xs font-semibold uppercase tracking-wider text-[#94A3B8]"
                  >
                    Active Voice Agent
                  </label>
                  <p className="text-xs text-[#F5F7FC]">
                    Switch between deployed AI agents to view their call logs.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="relative min-w-[240px]">
                  <select
                    id="agent-select"
                    value={selectedAgentId ?? ""}
                    onChange={(event) =>
                      setSelectedAgentId(Number(event.target.value))
                    }
                    className="w-full appearance-none rounded-lg border border-[#273449] bg-[#0E1528] px-3.5 py-2 pr-10 text-sm font-medium text-[#F5F7FC] outline-none transition focus:border-[#7657F6] focus:ring-2 focus:ring-[#7657F6]/20"
                  >
                    {agents.map((agent) => (
                      <option key={agent.id} value={agent.id}>
                        {agent.name} {agent.is_active ? "(Active)" : "(Inactive)"}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#94A3B8]" />
                </div>

                {selectedAgent && (
                  <StatusBadge
                    status={selectedAgent.is_active ? "active" : "inactive"}
                  />
                )}
              </div>
            </div>

            {selectedAgentId !== null && (
              <AgentCallList agentId={selectedAgentId} />
            )}
          </div>
        )}
      </PageContainer>
    </DashboardLayout>
  );
}
