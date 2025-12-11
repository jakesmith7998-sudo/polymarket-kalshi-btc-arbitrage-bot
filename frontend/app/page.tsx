"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { AlertCircle, TrendingUp } from "lucide-react"

interface MarketData {
  timestamp: string
  polymarket: {
    price_to_beat: number
    current_price: number
    prices: {
      Up: number
      Down: number
    }
    slug: string
  }
  kalshi: {
    event_ticker: string
    current_price: number
    markets: Array<{
      strike: number
      yes_ask: number
      no_ask: number
      subtitle: string
    }>
  }
  checks: Array<{
    kalshi_strike: number
    type: string
    poly_leg: string
    kalshi_leg: string
    poly_cost: number
    kalshi_cost: number
    total_cost: number
    is_arbitrage: boolean
    margin: number
  }>
  opportunities: Array<any>
  errors: string[]
}
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
import { RotateCcw, TrendingUp, DollarSign } from "lucide-react";

export default function Dashboard() {
  const [data, setData] = useState<MarketData | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())

  const fetchData = async () => {
    try {
      const res = await fetch("http://localhost:8000/arbitrage")
      const json = await res.json()
      setData(json)
      setLastUpdated(new Date())
      setLoading(false)
    } catch (err) {
      console.error("Failed to fetch data", err)
    }
  }
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 1000)
    return () => clearInterval(interval)
  }, [])

  if (loading) return <div className="flex items-center justify-center h-screen">Loading...</div>

  if (!data) return <div className="p-8">No data available</div>
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

  const bestOpp = data.opportunities.length > 0
    ? data.opportunities.reduce((prev, current) => (prev.margin > current.margin) ? prev : current)
    : null
  const { market, portfolio, last_action } = data;
  
  const yesPrice = market.prices?.Up || 0;
  const noPrice = market.prices?.Down || 0;
  const pairCost = portfolio.pair_cost;
  const isProfitable = pairCost > 0 && pairCost < 1.0;

  return (
    <div className="p-8 space-y-8 bg-slate-50 min-h-screen">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold tracking-tight">Arbitrage Bot Dashboard</h1>
          <Badge variant="outline" className="animate-pulse bg-green-100 text-green-800 border-green-200">
            <span className="w-2 h-2 rounded-full bg-green-500 mr-2"></span>
            Live
          </Badge>
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6 font-sans">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            Gabagool Arbitrage Bot
          </h1>
          <p className="text-zinc-400 mt-1">15m Timeframe • Asymmetric Accumulation Strategy</p>
        </div>
        <div className="text-sm text-muted-foreground">
          Last updated: {lastUpdated.toLocaleTimeString()}
        <div className="flex items-center gap-4">
          <Badge variant="outline" className="text-zinc-400 border-zinc-700 px-3 py-1">
            Status: <span className="text-emerald-400 ml-2">RUNNING</span>
          </Badge>
          <Button variant="destructive" size="sm" onClick={handleReset}>
            <RotateCcw className="w-4 h-4 mr-2" /> Reset Sim
          </Button>
        </div>
      </div>

      {data.errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md flex items-start gap-2">
          <AlertCircle className="h-5 w-5 mt-0.5" />
          <div>
            <strong className="font-bold block mb-1">Errors Detected:</strong>
            <ul className="list-disc ml-5 text-sm">
              {data.errors.map((err, i) => (
                <li key={i}>{err}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Best Opportunity Hero Card */}
      {bestOpp && (
        <Card className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-200 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2 text-green-700">
              <TrendingUp className="h-5 w-5" />
              <CardTitle>Best Opportunity Found</CardTitle>
            </div>
            <CardDescription>Risk-free arbitrage detected with highest margin</CardDescription>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* MARKET STATUS */}
        <Card className="lg:col-span-2 bg-zinc-900 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg font-medium text-zinc-200">Active Market</CardTitle>
            <Badge className="bg-blue-900/50 text-blue-200 border-blue-800">{market.slug}</Badge>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
              <div className="text-center md:text-left">
                <div className="text-sm text-muted-foreground">Profit Margin</div>
                <div className="text-4xl font-bold text-green-700">${bestOpp.margin.toFixed(3)}</div>
                <div className="text-xs text-green-600 font-medium">per unit</div>
            <div className="grid grid-cols-2 gap-4 mt-2">
              <div className="p-4 rounded-lg bg-emerald-950/30 border border-emerald-900/50">
                <div className="text-zinc-400 text-sm mb-1">Buy YES</div>
                <div className="text-4xl font-mono font-bold text-emerald-400">${yesPrice.toFixed(3)}</div>
              </div>

              <div className="flex-1 bg-white p-4 rounded-lg border border-green-100 w-full">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-semibold text-slate-700">Strategy</span>
                  <Badge className="bg-green-600">Buy Both</Badge>
                </div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Polymarket {bestOpp.poly_leg}</span>
                  <span className="font-mono">${bestOpp.poly_cost.toFixed(3)}</span>
                </div>
                <div className="flex justify-between text-sm mb-3">
                  <span>Kalshi {bestOpp.kalshi_leg} (${bestOpp.kalshi_strike.toLocaleString()})</span>
                  <span className="font-mono">${bestOpp.kalshi_cost.toFixed(3)}</span>
                </div>
                <div className="pt-2 border-t border-dashed border-slate-200 flex justify-between font-bold">
                  <span>Total Cost</span>
                  <span>${bestOpp.total_cost.toFixed(3)}</span>
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
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Polymarket Card */}
        <Card>
          <CardHeader>
            <CardTitle>Polymarket</CardTitle>
            <CardDescription>Target: {data.polymarket.slug}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-100 p-3 rounded-md">
                  <div className="text-xs text-muted-foreground uppercase font-bold">Price to Beat</div>
                  <div className="text-xl font-mono font-semibold">${data.polymarket.price_to_beat?.toLocaleString()}</div>
                </div>
                <div className="bg-slate-100 p-3 rounded-md">
                  <div className="text-xs text-muted-foreground uppercase font-bold">Current Price</div>
                  <div className="text-xl font-mono font-semibold">${data.polymarket.current_price?.toLocaleString()}</div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-center text-sm">
                  <span>UP Contract</span>
                  <span className="font-mono font-medium">${data.polymarket.prices.Up?.toFixed(3)}</span>
        {/* STRATEGY HEALTH */}
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader><CardTitle className="text-zinc-200">Pair Cost Strategy</CardTitle></CardHeader>
          <CardContent className="space-y-6">
            <div className="text-center py-4">
                <div className="text-zinc-500 text-sm mb-2 uppercase tracking-wider">Avg YES + Avg NO</div>
                <div className={`text-6xl font-black ${isProfitable ? "text-emerald-400" : "text-zinc-500"}`}>
                    ${pairCost.toFixed(3)}
                </div>
                <Progress value={data.polymarket.prices.Up * 100} className="h-2 bg-slate-100" indicatorClassName="bg-green-500" />

                <div className="flex justify-between items-center text-sm mt-2">
                  <span>DOWN Contract</span>
                  <span className="font-mono font-medium">${data.polymarket.prices.Down?.toFixed(3)}</span>
                <div className="text-xs text-zinc-500 mt-2">Target: &lt; $1.00</div>
            </div>
            <div className="space-y-2">
                <div className="flex justify-between text-sm">
                    <span className="text-zinc-400">Locked Profit</span>
                    <span className="text-emerald-400 font-bold">+${portfolio.locked_profit.toFixed(2)}</span>
                </div>
                <Progress value={data.polymarket.prices.Down * 100} className="h-2 bg-slate-100" indicatorClassName="bg-red-500" />
              </div>
                <Progress value={(portfolio.locked_profit / 10) * 100} className="h-2 bg-zinc-800" />
            </div>
          </CardContent>
        </Card>

        {/* Kalshi Card */}
        <Card>
          <CardHeader>
            <CardTitle>Kalshi</CardTitle>
            <CardDescription>Ticker: {data.kalshi.event_ticker}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="bg-slate-100 p-3 rounded-md mb-4">
                <div className="text-xs text-muted-foreground uppercase font-bold">Current Price</div>
                <div className="text-xl font-mono font-semibold">${data.kalshi.current_price?.toLocaleString()}</div>
              </div>
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

              <div className="space-y-3 max-h-[200px] overflow-y-auto pr-2">
                {data.kalshi.markets
                  .filter(m => Math.abs(m.strike - data.polymarket.price_to_beat) < 2500)
                  .map((m, i) => (
                    <div key={i} className="text-sm border-b pb-2 last:border-0">
                      <div className="flex justify-between font-medium mb-1">
                        <span>{m.subtitle}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>Yes: {m.yes_ask}¢</span>
                          <span>No: {m.no_ask}¢</span>
                        </div>
                        <div className="flex h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                          <div className="bg-green-500 h-full" style={{ width: `${m.yes_ask}%` }}></div>
                          <div className="bg-red-500 h-full" style={{ width: `${m.no_ask}%` }}></div>
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </CardContent>
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

      {/* Arbitrage Checks Table */}
      <Card>
        <CardHeader>
          <CardTitle>Arbitrage Analysis</CardTitle>
          <CardDescription>Real-time comparison of all potential strategies</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[100px]">Type</TableHead>
                <TableHead>Kalshi Strike</TableHead>
                <TableHead>Strategy</TableHead>
                <TableHead>Cost Analysis</TableHead>
                <TableHead className="text-right">Total Cost</TableHead>
                <TableHead className="text-right">Result</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.checks.map((check, i) => {
                const isProfitable = check.total_cost < 1.00
                const percentCost = Math.min(check.total_cost * 100, 100)

                return (
                  <TableRow key={i} className={isProfitable ? "bg-green-50/50" : ""}>
                    <TableCell>
                      <Badge variant="outline" className="whitespace-nowrap">
                        {check.type.replace("Poly", "P").replace("Kalshi", "K")}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      ${check.kalshi_strike.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-xs">
                      <div className="flex flex-col">
                        <span>Buy P-{check.poly_leg}</span>
                        <span>Buy K-{check.kalshi_leg}</span>
                      </div>
                    </TableCell>
                    <TableCell className="w-[30%]">
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>${check.poly_cost.toFixed(3)} + ${check.kalshi_cost.toFixed(3)}</span>
                          <span>{Math.round(check.total_cost * 100)}%</span>
                        </div>
                        <Progress
                          value={percentCost}
                          className="h-2"
                          indicatorClassName={isProfitable ? "bg-green-500" : "bg-slate-400"}
                        />
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-mono font-bold">
                      ${check.total_cost.toFixed(3)}
                    </TableCell>
                    <TableCell className="text-right">
                      {isProfitable ? (
                        <Badge className="bg-green-600 hover:bg-green-700 whitespace-nowrap">
                          +${check.margin.toFixed(3)}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground text-xs">-</span>
                      )}
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
  );
}
