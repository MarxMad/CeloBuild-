"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Trophy, TrendingUp, Users } from "lucide-react";

const LEADERBOARD_DATA = [
  { rank: 1, user: "vitalik.eth", score: 98, reward: "Rare NFT", avatar: "🟣" },
  { rank: 2, user: "dwr.eth", score: 95, reward: "5 cUSD", avatar: "🎩" },
  { rank: 3, user: "ccarella.eth", score: 92, reward: "Common Loot", avatar: "🍀" },
  { rank: 4, user: "jesse.xyz", score: 88, reward: "Common Loot", avatar: "🔵" },
];

const ACTIVE_TRENDS = [
  { id: 1, name: "Base vs Celo", posts: "1.2k", rewardPool: "$500" },
  { id: 2, name: "Frame Friday", posts: "850", rewardPool: "NFT Gen 1" },
];

export function Leaderboard() {
  return (
    <div className="grid gap-6 md:grid-cols-2 animate-in fade-in slide-in-from-bottom-8 duration-700">
      {/* Active Trends */}
      <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-[#FCFF52]" />
            <CardTitle className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
              Tendencias Activas
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {ACTIVE_TRENDS.map((trend) => (
            <div key={trend.id} className="flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors cursor-pointer border border-transparent hover:border-[#FCFF52]/30">
              <div>
                <div className="font-bold text-sm text-foreground">#{trend.name}</div>
                <div className="text-[10px] text-muted-foreground">{trend.posts} posts</div>
              </div>
              <div className="text-right">
                <div className="text-[10px] uppercase font-bold text-[#FCFF52] bg-[#FCFF52]/10 px-2 py-1 rounded-full">
                  {trend.rewardPool}
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Winners Leaderboard */}
      <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Trophy className="w-4 h-4 text-yellow-500" />
            <CardTitle className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
              Top Ganadores (24h)
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {LEADERBOARD_DATA.map((winner) => (
            <div key={winner.rank} className="flex items-center justify-between p-2">
              <div className="flex items-center gap-3">
                <div className={`w-6 h-6 flex items-center justify-center rounded-full text-xs font-bold ${
                    winner.rank === 1 ? 'bg-yellow-500 text-black' : 
                    winner.rank === 2 ? 'bg-gray-400 text-black' : 
                    winner.rank === 3 ? 'bg-orange-700 text-white' : 'bg-white/10 text-muted-foreground'
                }`}>
                    {winner.rank}
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-lg">{winner.avatar}</span>
                    <span className="text-sm font-medium">{winner.user}</span>
                </div>
              </div>
              <div className="text-right">
                 <span className="text-xs font-mono text-[#FCFF52]">{winner.score} pts</span>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
