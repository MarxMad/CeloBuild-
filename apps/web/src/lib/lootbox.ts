export type LootboxEventPayload = {
  frameId: string;
  channelId: string;
  trendScore: number;
  threadId?: string;
  targetAddress?: string; // Optional for demo
  rewardType?: "nft" | "cusd" | "xp";
};

export type AgentRunResponse = {
  thread_id: string;
  summary: string;
  tx_hash?: string;
  explorer_url?: string;
  mode?: string;
  reward_type?: "nft" | "cusd" | "xp";
};

export const DEFAULT_EVENT: LootboxEventPayload = {
  frameId: "frame-demo",
  channelId: "builders",
  trendScore: 0.93,
  rewardType: "nft",
};

