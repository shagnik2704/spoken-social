import { useState, useEffect } from 'react'
import { useUserStore } from '@/store/userStore'
import api from '@/lib/axios'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Loader2, ClipboardList, Info } from 'lucide-react'
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"

interface AnalysisData {
    [collegeName: string]: {
        [tutorialNumber: number]: number
    }
}

export function MiniTaskAnalysis() {
    const [data, setData] = useState<AnalysisData>({})
    const [isLoading, setIsLoading] = useState(true)
    const activeCourseId = useUserStore(state => state.activeCourseId)
    const activeBatchId = useUserStore(state => state.activeBatchId)

    useEffect(() => {
        setIsLoading(true)
        api.get('/api/admin/minitask-analysis', {
            params: { course_id: activeCourseId, batch_id: activeBatchId }
        })
        .then(res => {
            setData(res.data)
            setIsLoading(false)
        })
        .catch(err => {
            console.error('Failed to fetch minitask analysis', err)
            setIsLoading(false)
        })
    }, [activeCourseId, activeBatchId])

    if (isLoading) {
        return (
            <div className="flex items-center justify-center p-12">
                <Loader2 className="w-6 h-6 animate-spin text-primary" />
            </div>
        )
    }

    const colleges = Object.keys(data).sort()
    // Find all tutorial numbers present in the data
    const tutorialNums = Array.from(new Set(
        Object.values(data).flatMap(tuts => Object.keys(tuts).map(Number))
    )).sort((a, b) => a - b)

    if (colleges.length === 0) {
        return (
            <Card className="bg-card/50 border-dashed">
                <CardContent className="py-10 flex flex-col items-center justify-center text-muted-foreground">
                    <ClipboardList className="w-8 h-8 mb-2 opacity-20" />
                    <p className="text-sm font-medium">No minitask data found for this batch.</p>
                </CardContent>
            </Card>
        )
    }

    return (
        <Card className="border-none shadow-none bg-transparent">
            <CardHeader className="px-0 pt-0 pb-6">
                <div className="flex items-center gap-2">
                    <CardTitle className="text-xl font-bold tracking-tight">MiniTask EOI Analysis</CardTitle>
                    <TooltipProvider>
                        <Tooltip>
                            <TooltipTrigger>
                                <Info className="w-4 h-4 text-muted-foreground" />
                            </TooltipTrigger>
                            <TooltipContent>
                                <p className="max-w-xs text-xs">This table shows the number of learners from each college who opted for MiniTasks across different tutorials.</p>
                            </TooltipContent>
                        </Tooltip>
                    </TooltipProvider>
                </div>
                <CardDescription>Detailed breakdown of learner interest in minitasks per college and tutorial.</CardDescription>
            </CardHeader>
            <CardContent className="px-0">
                <div className="relative overflow-x-auto rounded-xl border border-border bg-card">
                    <table className="w-full text-sm text-left">
                        <thead className="text-xs uppercase tracking-wider text-muted-foreground bg-muted/50 border-b">
                            <tr>
                                <th className="px-6 py-4 font-bold sticky left-0 bg-muted/80 backdrop-blur-sm z-10 border-r min-w-[240px]">College Name</th>
                                {tutorialNums.map(num => (
                                    <th key={num} className="px-4 py-4 font-bold text-center border-r last:border-r-0">Tut #{num}</th>
                                ))}
                                <th className="px-6 py-4 font-bold text-center bg-primary/5 text-primary">Total</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y border-b">
                            {colleges.map(college => {
                                let rowTotal = 0
                                return (
                                    <tr key={college} className="hover:bg-muted/30 transition-colors group">
                                        <td className="px-6 py-4 font-semibold text-foreground sticky left-0 bg-card group-hover:bg-muted/30 z-10 border-r min-w-[240px]">
                                            {college}
                                        </td>
                                        {tutorialNums.map(num => {
                                            const count = data[college][num] || 0
                                            rowTotal += count
                                            return (
                                                <td key={num} className="px-4 py-4 text-center border-r last:border-r-0">
                                                    {count > 0 ? (
                                                        <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-bold text-xs">
                                                            {count}
                                                        </span>
                                                    ) : (
                                                        <span className="text-muted-foreground/30">—</span>
                                                    )}
                                                </td>
                                            )
                                        })}
                                        <td className="px-6 py-4 text-center font-bold bg-primary/5 text-primary">
                                            {rowTotal}
                                        </td>
                                    </tr>
                                )
                            })}
                        </tbody>
                        <tfoot className="bg-muted/20">
                            <tr className="font-bold">
                                <td className="px-6 py-4 sticky left-0 bg-muted/40 z-10 border-r">Tutorial Totals</td>
                                {tutorialNums.map(num => {
                                    const colTotal = colleges.reduce((sum, col) => sum + (data[col][num] || 0), 0)
                                    return (
                                        <td key={num} className="px-4 py-4 text-center border-r last:border-r-0">
                                            {colTotal}
                                        </td>
                                    )
                                })}
                                <td className="px-6 py-4 text-center bg-primary/10 text-primary">
                                    {colleges.reduce((sum, col) => sum + Object.values(data[col]).reduce((s, c) => s + c, 0), 0)}
                                </td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
            </CardContent>
        </Card>
    )
}
