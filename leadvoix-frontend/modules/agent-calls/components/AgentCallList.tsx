"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  PhoneCall,
  PhoneOutgoing,
  Clock,
  Sparkles,
  FileText,
  Volume2,
  X,
  TrendingUp,
  AlertTriangle,
  Lightbulb,
  Calendar,
} from "lucide-react";

import {
  analyzeAgentCall,
  createAgentCall,
  getAgentCalls,
  initiateAgentCall,
} from "../api/agentCallApi";

import {
  AgentCall,
  AgentCallIntelligence,
} from "../types/agentCall.types";
import {
  PrimaryButton,
  SecondaryButton,
  StatusBadge,
  EmptyState,
} from "@/components/crm";

interface AgentCallListProps {
  agentId: number;
}

function formatCallDuration(seconds: number | null | undefined): string {
  if (!seconds || seconds <= 0) return "0s";
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  if (mins === 0) return `${secs}s`;
  if (secs === 0) return `${mins}m`;
  return `${mins}m ${secs}s`;
}

export default function AgentCallList({ agentId }: AgentCallListProps) {
  const [selectedCall, setSelectedCall] = useState<AgentCall | null>(null);
  const [intelligence, setIntelligence] = useState<AgentCallIntelligence | null>(null);

  const [phoneNumber, setPhoneNumber] = useState("");
  const [callError, setCallError] = useState<string | null>(null);
  const [callSuccess, setCallSuccess] = useState<string | null>(null);

  const [intelligenceByCall, setIntelligenceByCall] = useState<
    Record<number, AgentCallIntelligence>
  >({});

  const {
    data: calls,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["agent-calls", agentId],
    queryFn: () => getAgentCalls(agentId),
    enabled: !!agentId,
  });

  const makeCallMutation = useMutation({
    mutationFn: async (toNumber: string) => {
      const agentCall = await createAgentCall(agentId, {
        caller_phone: toNumber,
        direction: "outbound",
      });

      const initiatedCall = await initiateAgentCall(
        agentId,
        agentCall.id,
        toNumber
      );

      return initiatedCall;
    },
    onSuccess: async () => {
      setPhoneNumber("");
      setCallError(null);
      setCallSuccess("Outbound call dispatched. Telephony carrier will connect shortly.");
      await refetch();
    },
    onError: (error: unknown) => {
      console.error("Failed to initiate AI call:", error);
      setCallSuccess(null);

      const errObj = error as { response?: { data?: { detail?: unknown } } };
      const detail = errObj?.response?.data?.detail;

      if (Array.isArray(detail)) {
        setCallError(
          detail
            .map((item: { msg?: string }) => item?.msg || "Validation error")
            .join(", ")
        );
      } else if (typeof detail === "string") {
        setCallError(detail);
      } else {
        setCallError("Failed to initiate call. Check telephone carrier logs or number formatting.");
      }
    },
  });

  const analyzeMutation = useMutation({
    mutationFn: (callId: number) => analyzeAgentCall(agentId, callId),
    onSuccess: (data) => {
      setIntelligence(data);
      setIntelligenceByCall((prev) => ({
        ...prev,
        [data.agent_call_id]: data,
      }));
    },
    onError: (error) => {
      console.error("Call intelligence analysis failed:", error);
    },
  });

  const handleViewDetails = (call: AgentCall) => {
    setSelectedCall(call);
    setIntelligence(intelligenceByCall[call.id] ?? null);
    analyzeMutation.reset();
  };

  const handleMakeCall = () => {
    const number = phoneNumber.trim();
    setCallError(null);
    setCallSuccess(null);

    if (!number) {
      setCallError("Please enter a customer phone number.");
      return;
    }

    if (!/^\+?[1-9]\d{7,14}$/.test(number)) {
      setCallError(
        "Please enter a valid E.164 phone number with country code, e.g. +14155552671 or +919876543210."
      );
      return;
    }

    makeCallMutation.mutate(number);
  };

  const handleAnalyzeCall = () => {
    if (!selectedCall) return;
    analyzeMutation.mutate(selectedCall.id);
  };

  const closeDetails = () => {
    setSelectedCall(null);
    setIntelligence(null);
    analyzeMutation.reset();
  };

  if (isLoading) {
    return (
      <div className="rounded-xl border border-[#273449] bg-[#151D32] p-8 text-center text-sm text-[#94A3B8]">
        Loading telephony logs and call records...
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-6 text-sm text-rose-400">
        Failed to load calls for this agent. Please verify connection.
      </div>
    );
  }

  return (
    <>
      {/* OUTBOUND AI DIALER CARD */}
      <div className="mb-8 rounded-xl border border-[#7657F6]/30 bg-gradient-to-r from-[#151D32] to-[#1a1c38] p-6 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#7657F6]/10 border border-[#7657F6]/20 text-[#7657F6]">
            <PhoneOutgoing className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-[#F5F7FC]">
              Dispatch Autonomous AI Call
            </h2>
            <p className="mt-0.5 text-xs text-[#94A3B8]">
              Initiates an instant voice session connected to this agent via Twilio telephony.
            </p>
          </div>
        </div>

        <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label
              htmlFor="ai-call-phone"
              className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-[#94A3B8]"
            >
              Recipient Phone Number (E.164 format)
            </label>
            <input
              id="ai-call-phone"
              type="tel"
              value={phoneNumber}
              onChange={(event) => {
                setPhoneNumber(event.target.value);
                setCallError(null);
                setCallSuccess(null);
              }}
              placeholder="+14155552671"
              disabled={makeCallMutation.isPending}
              className="w-full rounded-lg border border-[#273449] bg-[#0E1528] px-4 py-2.5 font-mono text-sm text-[#F5F7FC] placeholder:text-[#94A3B8]/40 outline-none transition focus:border-[#7657F6] focus:ring-2 focus:ring-[#7657F6]/20 disabled:opacity-50"
            />
          </div>

          <PrimaryButton
            onClick={handleMakeCall}
            loading={makeCallMutation.isPending}
            className="sm:h-11 sm:px-6"
          >
            <PhoneCall className="h-4 w-4" />
            Dispatch AI Call
          </PrimaryButton>
        </div>

        {callError && (
          <div className="mt-4 rounded-lg border border-rose-500/20 bg-rose-500/10 p-3 text-xs text-rose-400">
            {callError}
          </div>
        )}

        {callSuccess && (
          <div className="mt-4 rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3 text-xs text-emerald-400">
            {callSuccess}
          </div>
        )}
      </div>

      {/* CALL HISTORY */}
      <div className="overflow-hidden rounded-xl border border-[#273449] bg-[#151D32] shadow-sm">
        <div className="flex items-center justify-between border-b border-[#273449] px-6 py-4">
          <div>
            <h2 className="text-base font-semibold text-[#F5F7FC]">
              Call Sessions
            </h2>
            <p className="mt-0.5 text-xs text-[#94A3B8]">
              Telephony history, duration, and intelligence for this agent.
            </p>
          </div>
          <span className="font-mono text-xs text-[#94A3B8]">
            Total: {calls?.length ?? 0}
          </span>
        </div>

        {(!calls || calls.length === 0) ? (
          <EmptyState
            title="No call sessions recorded"
            description="This agent has not conducted any outbound or inbound calls yet. Use the dialer above to launch a test session."
            icon={PhoneCall}
          />
        ) : (
          <div className="divide-y divide-[#273449]">
            {calls.map((call) => (
              <div
                key={call.id}
                className="p-6 transition hover:bg-[#1E293B]/30"
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium text-[#F5F7FC]">
                        {call.caller_name || "Unknown Prospect"}
                      </h3>
                      <span className="rounded bg-[#0E1528] border border-[#273449] px-2 py-0.5 font-mono text-[11px] text-[#94A3B8]">
                        #{call.id}
                      </span>
                    </div>
                    <p className="mt-1 font-mono text-xs text-[#24C8D8]">
                      {call.caller_phone || "No phone number recorded"}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <StatusBadge status={call.status} />
                    <span className="rounded-full bg-[#0E1528] border border-[#273449] px-2.5 py-0.5 text-xs font-semibold capitalize text-[#94A3B8]">
                      {call.direction}
                    </span>
                  </div>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-4 rounded-lg border border-[#273449] bg-[#0E1528] p-3 text-xs sm:grid-cols-3">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-[#7657F6]" />
                    <div>
                      <span className="text-[#94A3B8]">Duration: </span>
                      <span className="font-mono font-medium text-[#F5F7FC]">
                        {formatCallDuration(call.duration)}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-[#94A3B8]" />
                    <div>
                      <span className="text-[#94A3B8]">Date: </span>
                      <span className="font-mono text-[#F5F7FC]">
                        {new Date(call.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  <div className="col-span-2 flex items-center justify-end gap-2 sm:col-span-1">
                    {call.recording_url && (
                      <a
                        href={call.recording_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 rounded border border-[#273449] bg-[#151D32] px-2.5 py-1 text-xs font-medium text-[#24C8D8] transition hover:bg-[#273449]"
                      >
                        <Volume2 className="h-3 w-3" />
                        Audio
                      </a>
                    )}
                    <SecondaryButton
                      size="sm"
                      onClick={() => handleViewDetails(call)}
                    >
                      <Sparkles className="h-3.5 w-3.5 text-[#7657F6]" />
                      Intelligence
                    </SecondaryButton>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* CALL DETAILS & INTELLIGENCE MODAL */}
      {selectedCall && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              closeDetails();
            }
          }}
        >
          <div className="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-2xl border border-[#273449] bg-[#151D32] shadow-2xl">
            {/* MODAL HEADER */}
            <div className="flex items-center justify-between border-b border-[#273449] px-6 py-5">
              <div>
                <div className="flex items-center gap-2.5">
                  <h2 className="text-lg font-bold text-[#F5F7FC]">
                    Call #{selectedCall.id}
                  </h2>
                  <StatusBadge status={selectedCall.status} />
                </div>
                <p className="mt-1 font-mono text-xs text-[#94A3B8]">
                  {selectedCall.caller_name || "Unknown Prospect"} ·{" "}
                  {selectedCall.caller_phone || "No phone number"}
                </p>
              </div>

              <button
                type="button"
                onClick={closeDetails}
                className="rounded-lg p-1.5 text-[#94A3B8] transition hover:bg-[#273449] hover:text-[#F5F7FC]"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* MODAL CONTENT */}
            <div className="space-y-6 p-6">
              {/* CALL METRICS */}
              <div className="grid grid-cols-2 gap-3 rounded-xl border border-[#273449] bg-[#0E1528] p-4 sm:grid-cols-4">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-[#94A3B8]">
                    Status
                  </p>
                  <p className="mt-1 font-medium capitalize text-[#F5F7FC]">
                    {selectedCall.status}
                  </p>
                </div>
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-[#94A3B8]">
                    Direction
                  </p>
                  <p className="mt-1 font-medium capitalize text-[#F5F7FC]">
                    {selectedCall.direction}
                  </p>
                </div>
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-[#94A3B8]">
                    Duration
                  </p>
                  <p className="mt-1 font-mono font-medium text-[#F5F7FC]">
                    {formatCallDuration(selectedCall.duration)}
                  </p>
                </div>
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-[#94A3B8]">
                    Initiated
                  </p>
                  <p className="mt-1 font-mono text-xs text-[#94A3B8]">
                    {new Date(selectedCall.created_at).toLocaleTimeString()}
                  </p>
                </div>
              </div>

              {/* RECORDING AUDIO PLAYER */}
              {selectedCall.recording_url && (
                <div>
                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">
                    Audio Recording
                  </h3>
                  <div className="rounded-xl border border-[#273449] bg-[#0E1528] p-4">
                    <audio
                      controls
                      className="w-full"
                      src={selectedCall.recording_url}
                    >
                      Your browser does not support audio playback.
                    </audio>
                  </div>
                </div>
              )}

              {/* TRANSCRIPT */}
              <div>
                <div className="mb-2 flex items-center gap-2">
                  <FileText className="h-4 w-4 text-[#7657F6]" />
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">
                    Dialogue Transcript
                  </h3>
                </div>
                <div className="max-h-60 overflow-y-auto rounded-xl border border-[#273449] bg-[#0E1528] p-4 font-mono text-xs leading-relaxed text-[#F5F7FC]">
                  {selectedCall.transcript ? (
                    <p className="whitespace-pre-wrap">{selectedCall.transcript}</p>
                  ) : (
                    <p className="text-[#94A3B8]">
                      No transcript recorded for this session.
                    </p>
                  )}
                </div>
              </div>

              {/* AI CALL INTELLIGENCE ACTION */}
              <div className="rounded-xl border border-[#7657F6]/30 bg-gradient-to-r from-[#151D32] to-[#1E293B] p-5">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-[#24C8D8]" />
                      <h3 className="text-sm font-semibold text-[#F5F7FC]">
                        AI Call Intelligence
                      </h3>
                    </div>
                    <p className="mt-1 text-xs text-[#94A3B8]">
                      Extract prospect sentiment, lead qualification score, objections, and deal recommendations.
                    </p>
                  </div>

                  <PrimaryButton
                    size="sm"
                    onClick={handleAnalyzeCall}
                    loading={analyzeMutation.isPending}
                  >
                    <Sparkles className="h-3.5 w-3.5" />
                    Analyze Session
                  </PrimaryButton>
                </div>

                {analyzeMutation.isError && (
                  <div className="mt-4 rounded-lg border border-rose-500/20 bg-rose-500/10 p-3 text-xs text-rose-400">
                    Failed to generate intelligence for this call. Please retry.
                  </div>
                )}
              </div>

              {/* AI INTELLIGENCE RESULTS */}
              {intelligence && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-[#273449] pb-2">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-[#24C8D8]">
                      Intelligence Insights
                    </h3>
                    <span className="rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-400">
                      Analysis Ready
                    </span>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    <div className="rounded-xl border border-[#273449] bg-[#0E1528] p-4">
                      <p className="text-[11px] font-semibold uppercase tracking-wider text-[#94A3B8]">
                        Lead Score
                      </p>
                      <p className="mt-1 font-mono text-3xl font-bold text-[#F5F7FC]">
                        {intelligence.lead_score}
                        <span className="text-sm font-normal text-[#94A3B8]">/100</span>
                      </p>
                    </div>

                    <div className="rounded-xl border border-[#273449] bg-[#0E1528] p-4">
                      <p className="text-[11px] font-semibold uppercase tracking-wider text-[#94A3B8]">
                        Sentiment
                      </p>
                      <p className="mt-2 text-base font-semibold capitalize text-[#F5F7FC]">
                        {intelligence.sentiment || "Neutral"}
                      </p>
                    </div>

                    <div className="rounded-xl border border-[#273449] bg-[#0E1528] p-4">
                      <p className="text-[11px] font-semibold uppercase tracking-wider text-[#94A3B8]">
                        Lead Temperature
                      </p>
                      <p className="mt-2 text-base font-semibold capitalize text-[#F5F7FC]">
                        {intelligence.lead_temperature || "Warm"}
                      </p>
                    </div>

                    <div className="rounded-xl border border-[#273449] bg-[#0E1528] p-4">
                      <p className="text-[11px] font-semibold uppercase tracking-wider text-[#94A3B8]">
                        Intent
                      </p>
                      <p className="mt-2 text-sm font-medium text-[#F5F7FC]">
                        {intelligence.customer_intent || "Evaluation"}
                      </p>
                    </div>
                  </div>

                  {intelligence.objections && (
                    <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
                      <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-amber-400">
                        <AlertTriangle className="h-3.5 w-3.5" />
                        Identified Objections
                      </div>
                      <p className="mt-2 text-xs leading-relaxed text-[#F5F7FC]">
                        {intelligence.objections}
                      </p>
                    </div>
                  )}

                  {intelligence.buying_signals && (
                    <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
                      <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-emerald-400">
                        <TrendingUp className="h-3.5 w-3.5" />
                        Buying Signals
                      </div>
                      <p className="mt-2 text-xs leading-relaxed text-[#F5F7FC]">
                        {intelligence.buying_signals}
                      </p>
                    </div>
                  )}

                  {intelligence.recommended_action && (
                    <div className="rounded-xl border border-[#7657F6]/30 bg-[#7657F6]/10 p-4">
                      <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-[#7657F6]">
                        <Lightbulb className="h-3.5 w-3.5" />
                        Recommended Next Step
                      </div>
                      <p className="mt-2 text-xs leading-relaxed text-[#F5F7FC]">
                        {intelligence.recommended_action}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="flex justify-end border-t border-[#273449] px-6 py-4">
              <SecondaryButton onClick={closeDetails}>
                Close
              </SecondaryButton>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
