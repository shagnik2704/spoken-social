import { AlertCircle, ArrowRight, ClipboardCheck, Download, FolderArchive, Loader2, Terminal } from 'lucide-react'
import { TerminalConsole } from '@/components/dashboard/TerminalConsole'
import { Button } from '@/components/ui/button'
import { parseLabTask, TERMINAL_MAX_CHARS, withXp } from '@/lib/learnerPack'
import { CommandChip } from '../CommandChip'
import type { TutorialStepProps } from '../types'

export const TerminalLabStep: React.FC<TutorialStepProps> = ({ detail, workspace, nav }) => {
    const task = parseLabTask(detail.content?.tryItInstructions || '')
    const isOverLimit = workspace.terminalOutput.length > TERMINAL_MAX_CHARS

    return (
        <div>
            <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
                <div className="lg:col-span-5 space-y-4">
                    <section className="rounded-xl bg-card border border-border shadow-xs overflow-hidden">
                        <div className="flex items-center gap-3 px-4 py-3 border-b border-border bg-teal/[0.06]">
                            <span className="size-9 shrink-0 rounded-lg bg-teal/15 text-teal flex items-center justify-center">
                                <Terminal className="size-4" />
                            </span>
                            <div className="min-w-0">
                                <p className="text-[11px] font-semibold uppercase tracking-wider text-teal">Lab assignment</p>
                                <h2 className="text-sm font-bold text-foreground">Run these commands in your Ubuntu terminal</h2>
                            </div>
                        </div>

                        <div className="p-4 space-y-4">
                            {task.intro && <p className="text-sm text-muted-foreground leading-relaxed">{task.intro}</p>}
                            <ol className="space-y-4">
                                {task.items.map((item, index) => (
                                    <li key={index} className="flex gap-3">
                                        <span className="size-6 shrink-0 rounded-full bg-primary/10 text-primary font-mono text-xs font-bold flex items-center justify-center">
                                            {index + 1}
                                        </span>
                                        <div className="min-w-0 flex-1 space-y-2">
                                            {item.text && <p className="text-sm text-foreground/90 leading-relaxed">{item.text}</p>}
                                            {item.commands.map(command => (
                                                <CommandChip key={command} command={command} />
                                            ))}
                                        </div>
                                    </li>
                                ))}
                            </ol>
                        </div>

                        {task.submit && (
                            <div className="flex gap-2.5 px-4 py-3 border-t border-border bg-primary/[0.04]">
                                <ClipboardCheck className="size-4 shrink-0 mt-0.5 text-primary" />
                                <p className="text-xs text-foreground/90 leading-relaxed">
                                    <span className="font-semibold text-foreground">What to submit: </span>
                                    {task.submit}
                                </p>
                            </div>
                        )}
                    </section>

                    {detail.codeFilesUrl && (
                        <div className="p-3 rounded-xl bg-card border border-border flex items-center justify-between gap-3 text-xs shadow-2xs">
                            <div className="flex items-center gap-2.5 text-foreground font-medium min-w-0">
                                <span className="size-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0">
                                    <FolderArchive className="size-4" />
                                </span>
                                <div className="truncate">
                                    <span className="block font-semibold truncate">Companion Code Files</span>
                                    <span className="text-[11px] text-muted-foreground">Practice datasets (.zip)</span>
                                </div>
                            </div>
                            <Button asChild size="sm" variant="outline" className="min-h-11 sm:min-h-8 text-xs gap-1.5 shrink-0 cursor-pointer">
                                <a href={detail.codeFilesUrl} download>
                                    <Download className="size-3.5" />
                                    <span>Download</span>
                                </a>
                            </Button>
                        </div>
                    )}

                    <div className="flex gap-2.5 p-3 rounded-xl bg-warning/10 border border-warning/20">
                        <AlertCircle className="size-4 shrink-0 mt-0.5 text-warning" />
                        <p className="text-xs text-muted-foreground leading-relaxed">
                            Paste the commands you ran and their output into the terminal box.{' '}
                            <strong className="text-foreground">Never paste real passwords.</strong>
                        </p>
                    </div>
                </div>

                {/* Right Column: Terminal */}
                <div className="lg:col-span-7 space-y-3">
                    <TerminalConsole
                        value={workspace.terminalOutput}
                        onChange={workspace.setTerminalOutput}
                        maxChars={TERMINAL_MAX_CHARS}
                        isSubmitted={Boolean(detail.userReflection)}
                        placeholder={"$ type exit\nexit is a shell builtin\n$ type cp\ncp is /usr/bin/cp\n$ ls\nDesktop  Documents  Downloads"}
                    />
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <p className="text-xs text-muted-foreground">
                            Paste the commands you ran with their output. Lines starting with <code className="font-terminal text-foreground">$</code> are highlighted as commands.
                        </p>
                        <div className="flex items-center gap-2 shrink-0">
                            {detail.userReflection && (
                                <Button
                                    variant="outline"
                                    onClick={() => nav.goToStep('quiz')}
                                    className="hidden lg:inline-flex text-xs gap-1.5 flex-1 sm:flex-none min-h-11 sm:min-h-9 cursor-pointer"
                                >
                                    <span>Take Quiz</span>
                                    <ArrowRight className="h-3.5 w-3.5" />
                                </Button>
                            )}
                            <Button
                                onClick={workspace.submitTerminal}
                                disabled={workspace.isSubmittingLab || !workspace.terminalOutput.trim() || isOverLimit}
                                className="font-semibold text-xs gap-1.5 flex-1 sm:flex-none min-h-11 sm:min-h-9 cursor-pointer"
                            >
                                {workspace.isSubmittingLab ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Terminal className="h-3.5 w-3.5" />}
                                <span>
                                    {workspace.isSubmittingLab ? 'Submitting...' : detail.userReflection ? 'Update Output' : withXp('Submit Commands', nav.xpFor('assignmentDone'))}
                                </span>
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
