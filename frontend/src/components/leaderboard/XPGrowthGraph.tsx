import { useEffect, useState, useMemo } from 'react'
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer,
} from 'recharts'
import { Card, CardContent } from '@/components/ui/card'
import { ChevronDown, TrendingUp, Zap } from 'lucide-react'
import { useLeaderboardStore } from '@/store/leaderboardStore'
import { useTheme } from '@/hooks/useTheme'

const MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]

function getAvailableMonths(): { label: string; value: string }[] {
    const now = new Date()
    const months: { label: string; value: string }[] = []
    // Show last 12 months including current
    for (let i = 0; i < 12; i++) {
        const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
        const year = d.getFullYear()
        const mon = d.getMonth()
        months.push({
            label: `${MONTH_NAMES[mon]} ${year}`,
            value: `${year}-${String(mon + 1).padStart(2, '0')}`,
        })
    }
    return months
}

function getCurrentMonth(): string {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

// Custom tooltip
function CustomTooltip({ active, payload, label }: any) {
    if (!active || !payload?.length) return null
    return (
        <div className="bg-card/95 backdrop-blur-sm border border-border/50 rounded-lg px-3 py-2 shadow-xl">
            <p className="text-[11px] text-muted-foreground mb-0.5">Day {label}</p>
            <p className="text-sm font-bold flex items-center gap-1">
                <Zap className="h-3.5 w-3.5 text-yellow-500" />
                {payload[0].value} XP
            </p>
        </div>
    )
}

export default function XPGrowthGraph() {
    const { xpHistory, fetchXPHistory } = useLeaderboardStore()
    const { theme } = useTheme()
    const [selectedMonth, setSelectedMonth] = useState(getCurrentMonth())
    const [dropdownOpen, setDropdownOpen] = useState(false)

    const axisColor = theme === 'dark' ? '#ffffff' : '#000000'
    const availableMonths = useMemo(() => getAvailableMonths(), [])

    useEffect(() => {
        fetchXPHistory(selectedMonth)
    }, [selectedMonth, fetchXPHistory])

    const totalXP = xpHistory.reduce((sum, d) => sum + d.xp, 0)
    const peakDay = xpHistory.reduce((max, d) => (d.xp > max.xp ? d : max), { day: 0, xp: 0 })
    const activeDays = xpHistory.filter(d => d.xp > 0).length

    const currentMonthLabel = availableMonths.find(m => m.value === selectedMonth)?.label || selectedMonth

    return (
        <Card className="border-border/40 overflow-hidden">
            <CardContent className="p-5 sm:p-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <TrendingUp className="h-5 w-5 text-primary" />
                        <h2 className="font-semibold">XP Growth</h2>
                    </div>

                    {/* Month Dropdown */}
                    <div className="relative">
                        <button
                            onClick={() => setDropdownOpen(!dropdownOpen)}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium
                                       bg-muted/40 hover:bg-muted/60 transition-colors border border-border/30"
                        >
                            {currentMonthLabel}
                            <ChevronDown className={`h-3 w-3 transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
                        </button>
                        {dropdownOpen && (
                            <div className="absolute right-0 top-full mt-1 w-48 bg-card border border-border rounded-lg shadow-xl z-20 py-1 max-h-64 overflow-y-auto">
                                {availableMonths.map(m => (
                                    <button
                                        key={m.value}
                                        onClick={() => { setSelectedMonth(m.value); setDropdownOpen(false) }}
                                        className={`w-full text-left px-3 py-2 text-sm transition-colors
                                                    ${selectedMonth === m.value
                                                ? 'bg-primary/10 text-primary font-medium'
                                                : 'hover:bg-muted/50 text-foreground'
                                            }`}
                                    >
                                        {m.label}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Stats Row */}
                <div className="grid grid-cols-3 gap-3 mb-4">
                    <div className="text-center p-2 rounded-lg bg-muted/20">
                        <p className="text-lg font-bold font-mono text-primary">{totalXP.toLocaleString()}</p>
                        <p className="text-[10px] text-muted-foreground">Total XP</p>
                    </div>
                    <div className="text-center p-2 rounded-lg bg-muted/20">
                        <p className="text-lg font-bold font-mono text-yellow-500">{peakDay.xp}</p>
                        <p className="text-[10px] text-muted-foreground">Peak (Day {peakDay.day})</p>
                    </div>
                    <div className="text-center p-2 rounded-lg bg-muted/20">
                        <p className="text-lg font-bold font-mono text-emerald-500">{activeDays}</p>
                        <p className="text-[10px] text-muted-foreground">Active Days</p>
                    </div>
                </div>

                {/* Chart */}
                <div className="h-52 sm:h-60">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={xpHistory} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                            <CartesianGrid
                                strokeDasharray="3 3"
                                stroke="hsl(var(--border))"
                                opacity={0.3}
                                vertical={false}
                            />
                            <XAxis
                                dataKey="day"
                                tick={{ fontSize: 10, fill: axisColor }}
                                tickLine={false}
                                axisLine={{ stroke: 'hsl(var(--border))', opacity: 0.3 }}
                                interval={4}
                            />
                            <YAxis
                                tick={{ fontSize: 10, fill: axisColor }}
                                tickLine={false}
                                axisLine={false}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <Line
                                type="monotone"
                                dataKey="xp"
                                stroke="#00E5FF"
                                strokeWidth={2.5}
                                dot={{ r: 3, fill: '#00E5FF', stroke: '#00E5FF' }}
                                activeDot={{
                                    r: 6,
                                    fill: '#00E5FF',
                                    stroke: 'hsl(var(--background))',
                                    strokeWidth: 2,
                                }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    )
}
