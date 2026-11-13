import { ArrowRight, CheckCircle2, ExternalLink, Loader2, UploadCloud } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { resolveMediaUrl } from '@/lib/learnerPack'
import { cn } from '@/lib/utils'
import type { TutorialStepProps } from '../types'

export const SetupVerificationStep: React.FC<TutorialStepProps> = ({ detail, workspace, nav }) => {
    const nextTutorial = nav.nextTutorial

    return (
        <div>
            <div className="max-w-4xl mx-auto space-y-6">
                <div className="p-4 sm:p-5 rounded-xl bg-card border border-border/80 shadow-xs flex items-center justify-between gap-4">
                    <p className="text-sm text-muted-foreground">
                        Set up your virtual machine, then upload a screenshot to complete this tutorial. Setup tutorials have no quiz.
                    </p>
                    <Badge variant="outline" className="shrink-0 bg-muted text-foreground border border-border font-mono font-semibold text-xs px-3 py-1">+15 XP</Badge>
                </div>

                {/* 3 Step Flow Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
                    <div className="p-4 rounded-xl bg-card border border-border/80 shadow-2xs space-y-1.5">
                        <div className="flex items-center gap-2">
                            <span className="size-6 rounded-full bg-primary/10 text-primary font-bold text-xs flex items-center justify-center">1</span>
                            <span className="text-xs font-bold text-foreground">Prepare & Install</span>
                        </div>
                        <p className="text-[11px] text-muted-foreground leading-relaxed">
                            {detail.tutorialNumber === 1
                                ? 'Check CPU virtualization in Task Manager, then download and install VirtualBox.'
                                : 'Download Ubuntu 24.04 ISO, create a VirtualBox VM, and boot the installer.'}
                        </p>
                    </div>
                    <div className="p-4 rounded-xl bg-card border border-border/80 shadow-2xs space-y-1.5">
                        <div className="flex items-center gap-2">
                            <span className="size-6 rounded-full bg-primary/10 text-primary font-bold text-xs flex items-center justify-center">2</span>
                            <span className="text-xs font-bold text-foreground">Open Verification View</span>
                        </div>
                        <p className="text-[11px] text-muted-foreground leading-relaxed">
                            {detail.tutorialNumber === 1
                                ? 'In VirtualBox Manager, open Help → About VirtualBox to show the version.'
                                : 'Boot into Ubuntu and open the desktop screen inside the VM window.'}
                        </p>
                    </div>
                    <div className="p-4 rounded-xl bg-card border border-border/80 shadow-2xs space-y-1.5">
                        <div className="flex items-center gap-2">
                            <span className="size-6 rounded-full bg-primary/10 text-primary font-bold text-xs flex items-center justify-center">3</span>
                            <span className="text-xs font-bold text-foreground">Upload Proof</span>
                        </div>
                        <p className="text-[11px] text-muted-foreground leading-relaxed">
                            Take a screenshot of the window and upload it below.
                        </p>
                    </div>
                </div>

                {/* Main Verification & Proof Area */}
                <div className="p-6 rounded-xl bg-card border border-border/90 shadow-sm space-y-5">
                    {/* If Already Submitted */}
                    {detail.userReflection?.imageUrl && !workspace.screenshotFile ? (
                        <div className="space-y-4">
                            <div className="p-4 rounded-xl bg-success/10 border border-success/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                                <div className="space-y-0.5">
                                    <div className="flex items-center gap-2 text-sm font-bold text-success">
                                        <CheckCircle2 className="h-4 w-4" />
                                        <span>Setup Screenshot Submitted & Recorded</span>
                                    </div>
                                    <p className="text-[11px] text-muted-foreground">
                                        Submitted on {new Date(detail.userReflection.submittedAt).toLocaleDateString()} • Recorded in your student lab portfolio (reviewed during course evaluation)
                                    </p>
                                </div>
                                <Badge variant="outline" className="bg-success/20 text-success border-success/40 text-xs font-semibold px-2.5 py-1 shrink-0 self-start sm:self-auto">
                                    ✓ Milestone Complete
                                </Badge>
                            </div>

                            {/* Screenshot Preview with clean framing and full-size link */}
                            <div className="rounded-xl overflow-hidden border border-border/80 bg-muted/40 p-3 text-center space-y-2">
                                <a
                                    href={resolveMediaUrl(detail.userReflection.imageUrl)}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="block group relative"
                                    title="Click to view full image in new tab"
                                >
                                    <img
                                        src={resolveMediaUrl(detail.userReflection.imageUrl)}
                                        alt="Setup Verification Screenshot"
                                        className="max-h-80 mx-auto rounded-lg object-contain shadow-xs group-hover:opacity-95 transition-opacity"
                                    />
                                    <div className="absolute bottom-2 right-2 px-2.5 py-1 rounded-md bg-black/70 text-white text-[11px] font-medium flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <ExternalLink className="h-3 w-3" />
                                        <span>Open full size</span>
                                    </div>
                                </a>
                                {detail.userReflection.reflectionText && (
                                    <p className="text-xs text-muted-foreground pt-1 italic font-sans">
                                        "{detail.userReflection.reflectionText}"
                                    </p>
                                )}
                            </div>

                            {/* Footer Actions */}
                            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 border-t">
                                <label className="text-xs font-semibold text-muted-foreground hover:text-foreground flex items-center gap-1.5 cursor-pointer">
                                    <UploadCloud className="h-4 w-4" />
                                    <span>Replace with another screenshot</span>
                                    <input
                                        type="file"
                                        accept="image/png,image/jpeg,image/webp"
                                        className="hidden"
                                        onChange={(e) => workspace.selectScreenshot(e.target.files?.[0])}
                                    />
                                </label>
                                {nextTutorial && (
                                    <Button
                                        onClick={() => nav.goToTutorial(nextTutorial.number)}
                                        className="min-h-11 sm:min-h-9 font-semibold text-xs gap-1.5 w-full sm:w-auto cursor-pointer"
                                    >
                                        <span>Proceed to Tutorial {nextTutorial.number}: {nextTutorial.title}</span>
                                        <ArrowRight className="h-3.5 w-3.5" />
                                    </Button>
                                )}
                            </div>
                        </div>
                    ) : (
                        /* If Not Yet Submitted or Re-uploading */
                        <div className="space-y-4">
                            <div className="flex items-center justify-between border-b pb-3">
                                <div>
                                    <h3 className="text-sm font-bold text-foreground">Upload Proof of Installation</h3>
                                    <p className="text-xs text-muted-foreground">
                                        {detail.tutorialNumber === 1
                                            ? 'Screenshot of VirtualBox Manager with Help → About window open showing installed version.'
                                            : 'Screenshot of Ubuntu 24.04 desktop running inside your Oracle VirtualBox window.'}
                                    </p>
                                </div>
                                <Badge variant="outline" className="bg-muted text-foreground border border-border font-mono font-semibold text-xs">+15 XP</Badge>
                            </div>

                            {/* Modern Upload Dropzone */}
                            <label className={cn(
                                "border border-dashed rounded-xl p-6 sm:p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-all",
                                workspace.screenshotPreview
                                    ? "border-primary/50 bg-primary/5"
                                    : "border-border/80 hover:border-primary/60 hover:bg-muted/40"
                            )}>
                                <input
                                    type="file"
                                    accept="image/png,image/jpeg,image/webp"
                                    className="hidden"
                                    onChange={(e) => workspace.selectScreenshot(e.target.files?.[0])}
                                />
                                {workspace.screenshotPreview ? (
                                    <div className="space-y-3">
                                        <img
                                            src={workspace.screenshotPreview}
                                            alt="Preview"
                                            className="max-h-64 mx-auto rounded-xl object-contain shadow-xs border"
                                        />
                                        <div className="text-xs text-foreground font-semibold flex items-center justify-center gap-2">
                                            <span>{workspace.screenshotFile?.name}</span>
                                            <Badge variant="outline" className="text-[11px]">
                                                {workspace.screenshotFile ? (workspace.screenshotFile.size / 1024).toFixed(0) + ' KB' : ''}
                                            </Badge>
                                        </div>
                                        <span className="text-[11px] text-primary hover:underline">Click to choose a different image</span>
                                    </div>
                                ) : (
                                    <div className="space-y-2.5">
                                        <div className="size-14 rounded-xl bg-primary/10 text-primary flex items-center justify-center mx-auto shadow-2xs">
                                            <UploadCloud className="h-7 w-7" />
                                        </div>
                                        <div className="text-sm font-semibold text-foreground">
                                            Click to select screenshot or drag and drop here
                                        </div>
                                        <p className="text-xs text-muted-foreground">
                                            Supports PNG, JPG, or WEBP (Maximum size: 5 MB)
                                        </p>
                                    </div>
                                )}
                            </label>

                            <div className="space-y-1.5">
                                <label className="text-xs font-semibold text-muted-foreground">
                                    Setup Notes / Machine Details (Optional)
                                </label>
                                <input
                                    type="text"
                                    value={workspace.screenshotNotes}
                                    onChange={(e) => workspace.setScreenshotNotes(e.target.value)}
                                    placeholder="e.g. Windows 11 64-bit, VirtualBox 7.0 installed smoothly"
                                    className="w-full text-xs p-2.5 rounded-xl border bg-background text-foreground"
                                />
                            </div>

                            <div className="flex items-center justify-between pt-2">
                                {workspace.screenshotFile && (
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="sm"
                                        onClick={workspace.clearScreenshot}
                                        className="min-h-11 sm:min-h-9 text-xs text-muted-foreground cursor-pointer"
                                    >
                                        Cancel
                                    </Button>
                                )}
                                <Button
                                    onClick={workspace.submitScreenshot}
                                    disabled={!workspace.screenshotFile || workspace.isSubmittingLab}
                                    className="min-h-11 sm:min-h-9 font-semibold text-xs ml-auto gap-2 cursor-pointer"
                                >
                                    {workspace.isSubmittingLab ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <UploadCloud className="h-3.5 w-3.5" />}
                                    <span>{workspace.isSubmittingLab ? 'Uploading...' : 'Submit Setup Screenshot (+15 XP)'}</span>
                                </Button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
