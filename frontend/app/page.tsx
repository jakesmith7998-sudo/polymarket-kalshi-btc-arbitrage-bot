"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { RotateCcw, TrendingUp, DollarSign, Wallet } from "lucide-react";

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
  
  // Backend now sends the real calculated values
  const cashBalance = portfolio.cash_balance;
  const totalEquity = portfolio.total_equity;
  const lockedProfit = portfolio.locked_profit;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6 font-sans">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            Gabagool Arbitrage Bot
          </h1>
          <p className="text-zinc-400 mt-1">15m Timeframe • Balance Check Enabled</p>
        </div>
        <div className="flex items-center gap-4">
          <Badge variant="outline" className="text-zinc-400 border-zinc-700 px-3 py-1">
            Status: <span className="text-emerald-400 ml-2">RUNNING</span>
          </Badge>
          <Button variant="destructive" size="sm" onClick={handleReset}>
            <RotateCcw className="w-4 h-4 mr-2" /> Manual Force Reset
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* WALLET / BALANCE CARD (NEW) */}
        <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader><CardTitle className="text-zinc-200 flex items-center gap-2"><Wallet className="w-5 h-5 text-yellow-400"/> Account Balance</CardTitle></CardHeader>
            <CardContent>
                <div className="space-y-4">
                    <div>
                        <div className="text-zinc-500 text-xs uppercase tracking-wider mb-1">Total Equity (Cash + Shares)</div>
                        <div className="text-4xl font-black text-white">${totalEquity.toFixed(3)}</div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 pt-2 border-t border-zinc-800">
                         <div>
                            <div className="text-zinc-500 text-xs">Available Cash</div>
                            <div className="text-xl font-mono text-emerald-400">${cashBalance.toFixed(2)}</div>
                         </div>
                         <div>
                            <div className="text-zinc-500 text-xs">Locked Profit</div>
                            <div className="text-xl font-mono text-blue-400">+${lockedProfit.toFixed(3)}</div>
                         </div>
                    </div>
                </div>
            </CardContent>
        </Card>

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

        {/* PORTFOLIO STATE */}
        <Card className="lg:col-span-3 bg-zinc-900 border-zinc-800">
            <CardHeader><CardTitle className="text-zinc-200 flex items-center gap-2"><DollarSign className="w-5 h-5 text-purple-400"/> Inventory</CardTitle></CardHeader>
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
                            <TableCell>{portfolio.qty_yes}</TableCell>
                            <TableCell>${portfolio.avg_cost_yes.toFixed(3)}</TableCell>
                            <TableCell>${(portfolio.qty_yes * portfolio.avg_cost_yes).toFixed(2)}</TableCell>
                        </TableRow>
                        <TableRow className="border-zinc-800 hover:bg-zinc-800/50">
                            <TableCell className="font-medium text-red-400">NO</TableCell>
                            <TableCell>{portfolio.qty_no}</TableCell>
                            <TableCell>${portfolio.avg_cost_no.toFixed(3)}</TableCell>
                            <TableCell>${(portfolio.qty_no * portfolio.avg_cost_no).toFixed(2)}</TableCell>
                        </TableRow>
                    </TableBody>
                </Table>
            </CardContent>
        </Card>

        {/* TRADE HISTORY */}
        <Card className="lg:col-span-3 bg-zinc-900 border-zinc-800">
            <CardHeader><CardTitle className="text-zinc-200 flex items-center gap-2"><TrendingUp className="w-5 h-5 text-blue-400"/> Live Trade Simulation</CardTitle></CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow className="border-zinc-800 hover:bg-zinc-900">
                            <TableHead className="text-zinc-400">Time</TableHead>
                            <TableHead className="text-zinc-400">Action</TableHead>
                            <TableHead className="text-zinc-400">Price</TableHead>
                            <TableHead className="text-zinc-400">Size</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {portfolio.history.slice().reverse().map((trade: any, i: number) => (
                            <TableRow key={i} className="border-zinc-800 hover:bg-zinc-800/50">
                                <TableCell className="font-mono text-zinc-500">{trade.timestamp}</TableCell>
                                <TableCell>
                                    <Badge variant="outline" className={
                                        trade.side === "YES" 
                                        ? "border-emerald-900 text-emerald-400 bg-emerald-950/20" 
                                        : "border-red-900 text-red-400 bg-red-950/20"
                                    }>
                                        Buy {trade.side}
                                    </Badge>
                                </TableCell>
                                <TableCell className="font-mono">${trade.price.toFixed(3)}</TableCell>
                                <TableCell>{trade.size}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
      </div>
    </div>
  );
}
