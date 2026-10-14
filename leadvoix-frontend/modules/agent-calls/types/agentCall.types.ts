export interface AgentCall {
  id: number;
  agent_id: number;
  organization_id: number;

  caller_name?: string | null;
  caller_phone?: string | null;

  status: string;
  direction: string;

  duration?: number | null;
  transcript?: string | null;
  recording_url?: string | null;
  provider_call_id?: string | null;

  started_at?: string | null;
  ended_at?: string | null;
  created_at: string;
}

export interface AgentCallCreate {
  caller_name?: string | null;
  caller_phone?: string | null;
  direction?: string;
}

export interface AgentCallUpdate {
  status?: string | null;
  duration?: number | null;
  transcript?: string | null;
  recording_url?: string | null;
  provider_call_id?: string | null;
  started_at?: string | null;
  ended_at?: string | null;
}

/**
 * Agent call list response
 *
 * Backend currently returns a list of calls.
 */
export type AgentCallListResponse = AgentCall[];

/**
 * AI intelligence generated from an agent call
 */
export interface AgentCallIntelligence {
  id?: number;
  agent_call_id: number;

  sentiment?: string | null;
  lead_score?: number | null;
  lead_temperature?: string | null;
  customer_intent?: string | null;
  recommended_action?: string | null;

  summary?: string | null;
  key_points?: string | null;
  outcome?: string | null;
  next_action?: string | null;

  objects?: Record<string, unknown> | null;
  objections?: string | null;
  buying_signals?: string[] | null;

}