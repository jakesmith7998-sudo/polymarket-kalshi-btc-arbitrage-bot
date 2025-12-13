"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { RotateCcw, TrendingUp, DollarSign } from "lucide-react";

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      fetch("http://localhost:8000/simulation")
        .then((res) => res.json())
        .then((data) => {
          setData(data);
          setLoading(false);
        })
        .catch((err) => console.error(err));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleReset = async () => {
    await fetch("http://localhost:8000/reset", { method: "POST" });
  };

  if (loading || !data || !data.market) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-zinc-950 text-white">
        <div className="text-xl animate-pulse">Initializing Gabagool Strategy...</div>
      </div>
    );
  }

  const { market, portfolio, last_action } = data;
  
  const yesPrice = market.prices?.Up || 0;
  const noPrice = market.prices?.Down || 0;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6 font-sans">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            Gabagool Arbitrage Bot
          </h1>
          <p className="text-zinc-400 mt-1">15m Timeframe • Scoreboard Mode</p>
        </div>
        <div className="flex items-center gap-4">
          <Badge variant="outline" className="text-zinc-400 border-zinc-700 px-3 py-1">
            Status: <span className="text-emerald-400 ml-2">RUNNING</span>
          </Badge>
          <Button variant="destructive" size="sm" onClick={handleReset}>
            <RotateCcw className="w-4 h-4 mr-2" /> Manual Reset
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* MARKET STATUS */}
        <Card className="lg:col-span-2 bg-zinc-900 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg font-medium text-zinc-200">Active Market</CardTitle>
            <Badge className="bg-blue-900/50 text-blue-200 border-blue-800">{market.slug}</Badge>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 mt-2">
              <div className="p-4 rounded-lg bg-emerald-950/30 border border-emerald-900/50">
                <div className="text-zinc-400 text-sm mb-1">Buy YES</div>
                <div className="text-4xl font-mono font-bold text-emerald-400">${yesPrice.toFixed(3)}</div>
              </div>
              <div className="p-4 rounded-lg bg-red-950/30 border border-red-900/50">
                <div className="text-zinc-400 text-sm mb-1">Buy NO</div>
                <div className="text-4xl font-mono font-bold text-red-400">${noPrice.toFixed(3)}</div>
              </div>
            </div>
            <div className="mt-6 flex items-center justify-between bg-zinc-950 p-3 rounded border border-zinc-800">
                <span className="text-zinc-400 text-sm">Last Action:</span>
                <span className="font-mono text-yellow-400">{last_action}</span>
            </div>
          </CardContent>
        </Card>

        {/* SCOREBOARD (Banked Profit) */}
        <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader><CardTitle className="text-zinc-200 flex items-center gap-2"><DollarSign className="w-5 h-5 text-purple-400"/> Daily Profit</CardTitle></CardHeader>
            <CardContent>
                <div className="flex flex-col items-center justify-center h-32">
                    <div className="text-zinc-500 text-sm uppercase tracking-wider mb-2">Total Banked</div>
                    <div className="text-5xl font-black text-emerald-400">
                        ${portfolio.locked_profit.toFixed(3)}
                    </div>
                </div>
            </CardContent>
        </Card>

        {/* INVENTORY */}
        <Card className="lg:col-span-3 bg-zinc-900 border-zinc-800">
            <CardHeader><CardTitle className="text-zinc-200 flex items-center gap-2"><TrendingUp className="w-5 h-5 text-blue-400"/> Current Inventory</CardTitle></CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow className="border-zinc-800 hover:bg-zinc-900">
                            <TableHead className="text-zinc-400">Side</TableHead>
                            <TableHead className="text-zinc-400">Shares</TableHead>
                            <TableHead className="text-zinc-400">Avg Cost</TableHead>
                            <TableHead className="text-zinc-400">Total Spent</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        <TableRow className="border-zinc-800 hover:bg-zinc-800/50">
                            <TableCell className="font-medium text-emerald-400">YES</TableCell>
                            <TableCell>{portfolio.qty_yes.toFixed(3)}</TableCell>
                            <TableCell>${portfolio.avg_cost_yes.toFixed(3)}</TableCell>
                            <TableCell>${(portfolio.qty_yes * portfolio.avg_cost_yes).toFixed(2)}</TableCell>
                        </TableRow>
                        <TableRow className="border-zinc-800 hover:bg-zinc-800/50">
                            <TableCell className="font-medium text-red-400">NO</TableCell>
                            <TableCell>{portfolio.qty_no.toFixed(3)}</TableCell>
                            <TableCell>${portfolio.avg_cost_no.toFixed(3)}</TableCell>
                            <TableCell>${(portfolio.qty_no * portfolio.avg_cost_no).toFixed(2)}</TableCell>
                        </TableRow>
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
      </div>
    </div>
  );
}
