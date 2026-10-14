import api from "@/lib/api/axios";

import {
  AgentCall,
  AgentCallCreate,
  AgentCallListResponse,
  AgentCallIntelligence,
} from "../types/agentCall.types";

/**
 * Get all calls for an agent
 */
export const getAgentCalls = async (
  agentId: number
): Promise<AgentCallListResponse> => {
  const response = await api.get(
    `/agents/${agentId}/calls`
  );

  return response.data;
};

/**
 * Create a new agent call
 */
export const createAgentCall = async (
  agentId: number,
  data: AgentCallCreate
): Promise<AgentCall> => {
  const response = await api.post(
    `/agents/${agentId}/calls`,
    data
  );

  return response.data;

};

/**
 * Initiate an agent call through the voice provider
 */
export const initiateAgentCall = async (
  agentId: number,
  callId: number,
  toNumber: string
): Promise<AgentCall> => {
  const response = await api.post(
    `/agents/${agentId}/calls/${callId}/initiate`,
    null,
    {
      params: {
        to_number: toNumber,
      },
    }
  );

  return response.data;
};

/**
 * Get a single agent call
 */
export const getAgentCall = async (
  agentId: number,
  callId: number
): Promise<AgentCall> => {
  const response = await api.get(
    `/agents/${agentId}/calls/${callId}`
  );

  return response.data;
};

/**
 * Get AI intelligence for a call
 */
export const getAgentCallIntelligence = async (
  agentId: number,
  callId: number
): Promise<AgentCallIntelligence> => {
  const response = await api.get(
    `/agents/${agentId}/calls/${callId}/intelligence`
  );

  return response.data;
};

/**
 * Analyze a call with AI
 */
export const analyzeAgentCall = async (
  agentId: number,
  callId: number
): Promise<AgentCallIntelligence> => {
  const response = await api.post(
    `/agents/${agentId}/calls/${callId}/intelligence`
  );

  return response.data;
};

/**
 * Get calls associated with a lead
 */
export const getLeadCalls = async (
  leadId: number
) => {
  const response = await api.get(
    `/leads/${leadId}/calls`
  );

  return response.data;
};