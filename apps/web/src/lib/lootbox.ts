export type LootboxEventPayload = {
  frameId?: string; // Opcional: el backend lo generará cuando detecte la tendencia
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
  user_analysis?: {
    username?: string;
    score?: number;
    follower_count?: number;
    power_badge?: boolean;
    reasons?: string[];
    participation?: {
      directly_participated?: boolean;
      total_engagement?: number;
      related_casts?: number;
    };
  };
  trend_info?: {
    source_text?: string;
    ai_analysis?: string;
    ai_enabled?: boolean; // true = usa Gemini AI, false = usa fallback básico
    trend_score?: number;
    topic_tags?: string[];
  };
  eligible?: boolean | null; // null = no verificado, true/false = resultado
  eligibility_message?: string; // Mensaje explicando por qué no es elegible
};

export const DEFAULT_EVENT: LootboxEventPayload = {
  frameId: "frame-demo",
  channelId: "builders",
  trendScore: 0.93,
  rewardType: "nft",
};

