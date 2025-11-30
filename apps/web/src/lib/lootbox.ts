export type LootboxEventPayload = {
  frameId: string;
  channelId: string;
  trendScore: number;
  threadId?: string;
};

export type AgentRunResponse = {
  thread_id: string;
  summary: string;
};

export const DEFAULT_EVENT: LootboxEventPayload = {
  frameId: "frame-demo",
  channelId: "builders",
  trendScore: 0.93,
};

