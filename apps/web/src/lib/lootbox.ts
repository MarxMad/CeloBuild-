export type LootboxEventPayload = {
  frameId: string;
  channelId: string;
  trendScore: number;
  threadId?: string;
  targetAddress?: string; // Optional for demo
};

export type AgentRunResponse = {
  thread_id: string;
  summary: string;
  tx_hash?: string;
  explorer_url?: string;
};

export const DEFAULT_EVENT: LootboxEventPayload = {
  frameId: "frame-demo",
  channelId: "builders",
  trendScore: 0.93,
};
