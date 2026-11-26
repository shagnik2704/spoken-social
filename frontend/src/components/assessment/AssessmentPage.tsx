import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { toast } from 'sonner'
import { ArrowLeft, CheckCircle2, ClipboardCheck, FileText, FlaskConical, GraduationCap, Paperclip, ShieldAlert } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { READING_COMPONENTS } from '@/components/tutorial/readingMarkdown'
import { useSyncActiveCourse } from '@/hooks/useSyncActiveCourse'
import api from '@/lib/axios'
import { assessmentLabel, coursePath, GEMINI_KEY_PATTERN, resolveMediaUrl } from '@/lib/learnerPack'
import { cn } from '@/lib/utils'
import { useLearnerPackStore } from '@/store/learnerPackStore'
import { useUserStore } from '@/store/userStore'
import type { AssessmentDetail } from '@/types'

const TEXT_MIN = 20
const TEXT_MAX = 20000
const FILE_MAX_BYTES = 10 * 1024 * 1024
const FILE_ACCEPT = '.csv,.txt,.py,.ipynb,.md,.pdf,.png,.jpg,.jpeg,.webp'

const errorDetail = (err: unknown): string | null => {
    if (!axios.isAxiosError(err)) return null
    const detail: unknown = err.response?.data?.detail
    return typeof detail === 'string' ? detail : null
}

const formatDate = (iso: string | null): string =>
    iso ? new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : ''

interface SubmissionFormProps {
    courseId: string
    assessment: AssessmentDetail
    onSaved: (next: AssessmentDetail) => void
}

const SubmissionForm: React.FC<SubmissionFormProps> = ({ courseId, assessment, onSaved }) => {
    const existing = assessment.submission
    const [text, setText] = useState(existing?.text ?? '')
    const [link, setLink] = useState(existing?.linkUrl ?? '')
    const [file, setFile] = useState<File | null>(null)
    const [isSaving, setIsSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const hasApiKey = GEMINI_KEY_PATTERN.test(text) || GEMINI_KEY_PATTERN.test(link)
    const label = assessmentLabel(assessment)

    const handleFile = (selected: File | undefined): void => {
        setError(null)
        if (!selected) return
        if (selected.size > FILE_MAX_BYTES) {
            setError('The file is larger than 10 MB.')
            return
        }
        setFile(selected)
    }

    const submit = async (event: React.FormEvent): Promise<void> => {
        event.preventDefault()
        const trimmed = text.trim()
        if (trimmed.length < TEXT_MIN) {
            setError('Write or paste your work before submitting.')
            return
        }
        if (hasApiKey) {
            setError('Remove your Gemini API key first. Keys are passwords.')
            return
        }
        const form = new FormData()
        form.append('submission_text', trimmed)
        if (link.trim()) form.append('link_url', link.trim())
        if (file) form.append('file', file)
        try {
            setIsSaving(true)
            setError(null)
            const res = await api.post<AssessmentDetail>(
                `/api/learner-pack/course/${courseId}/assessments/${assessment.key}/submission`,
                form,
                { headers: { 'Content-Type': 'multipart/form-data' } },
            )
            setFile(null)
            onSaved(res.data)
            toast.success(existing ? `${label} updated` : `${label} submitted`)
        } catch (err) {
            setError(errorDetail(err) ?? 'Your submission could not be saved. Try again.')
        } finally {
            setIsSaving(false)
        }
    }

    return (
        <form onSubmit={submit} className="space-y-4" noValidate>
            <div className="space-y-1.5">
                <div className="flex items-baseline justify-between gap-2">
                    <Label htmlFor="assessment-text" className="text-sm font-semibold">Your work</Label>
                    <span className="font-mono text-[11px] text-muted-foreground">{text.length.toLocaleString()} / {TEXT_MAX.toLocaleString()}</span>
                </div>
                <Textarea
                    id="assessment-text"
                    value={text}
                    onChange={(event) => { setText(event.target.value); setError(null) }}
                    maxLength={TEXT_MAX}
                    rows={10}
                    placeholder="Paste your prompts, answers, code or report here."
                    className="min-h-56 text-sm leading-6 transition duration-200 ease-in-out"
                />
            </div>

            <div className="space-y-1.5">
                <Label htmlFor="assessment-link" className="text-sm font-semibold">
                    Link <span className="font-normal text-muted-foreground">(optional)</span>
                </Label>
                <Input
                    id="assessment-link"
                    type="url"
                    inputMode="url"
                    value={link}
                    onChange={(event) => { setLink(event.target.value); setError(null) }}
                    placeholder="https://colab.research.google.com/…"
                    className="min-h-11 text-sm transition duration-200 ease-in-out"
                />
                <p className="text-[11px] text-muted-foreground">A Colab notebook or Google Drive file, shared so anyone with the link can view it.</p>
            </div>

            <div className="space-y-1.5">
                <Label htmlFor="assessment-file" className="text-sm font-semibold">
                    File <span className="font-normal text-muted-foreground">(optional)</span>
                </Label>
                <label
                    htmlFor="assessment-file"
                    className="flex items-center gap-3 min-h-11 px-3 py-2 rounded-lg border border-dashed border-border hover:border-teal/50 hover:bg-teal/[0.03] cursor-pointer transition duration-200 ease-in-out"
                >
                    <Paperclip className="size-4 shrink-0 text-teal" />
                    <span className="min-w-0 text-sm text-foreground truncate">
                        {file ? file.name : existing?.fileName ? `Replace ${existing.fileName}` : 'Choose a CSV, image, PDF or notebook'}
                    </span>
                </label>
                <input id="assessment-file" type="file" accept={FILE_ACCEPT} className="sr-only" onChange={(event) => handleFile(event.target.files?.[0])} />
                <p className="text-[11px] text-muted-foreground">Up to 10 MB.</p>
            </div>

            <p className={cn(
                'flex items-start gap-2 p-3 rounded-lg text-xs leading-5 border transition-colors duration-200 ease-in-out',
                hasApiKey ? 'bg-danger/10 border-danger/30 text-danger' : 'bg-warning/10 border-warning/25 text-foreground/80'
            )}>
                <ShieldAlert className={cn('size-4 shrink-0 mt-0.5', hasApiKey ? 'text-danger' : 'text-warning')} />
                {hasApiKey
                    ? 'This looks like a Gemini API key. Remove it before submitting: anyone who has it can use your account.'
                    : 'Never include your Gemini API key, passwords or other people’s private details.'}
            </p>

            {error && <p role="alert" className="text-sm font-medium text-danger">{error}</p>}

            <Button type="submit" disabled={isSaving} className="w-full min-h-11 font-semibold cursor-pointer transition duration-200 ease-in-out">
                {isSaving ? 'Saving…' : existing ? 'Update submission' : `Submit ${label.toLowerCase()}`}
            </Button>
        </form>
    )
}

const ReviewedSubmission: React.FC<{ assessment: AssessmentDetail }> = ({ assessment }) => {
    const submission = assessment.submission
    if (!submission) return null
    return (
        <div className="space-y-4">
            {(submission.score !== null || submission.feedback) && (
                <div className="p-3.5 rounded-lg bg-success/10 border border-success/25 space-y-1">
                    {submission.score !== null && (
                        <p className="text-sm font-semibold text-foreground">Score: <span className="font-mono">{submission.score}</span></p>
                    )}
                    {submission.feedback && <p className="text-sm text-foreground/85 whitespace-pre-wrap">{submission.feedback}</p>}
                </div>
            )}
            <pre className="max-h-80 overflow-auto p-3 rounded-lg bg-muted/50 border border-border text-xs leading-5 whitespace-pre-wrap font-sans">{submission.text}</pre>
        </div>
    )
}

const AssessmentPage: React.FC = () => {
    const { courseId = '', key = '' } = useParams()
    useSyncActiveCourse(courseId)
    const courseTitle = useUserStore(state => state.courses.find(course => course.id === courseId)?.title)
    const fetchOverview = useLearnerPackStore(state => state.fetchOverview)
    const endpoint = `/api/learner-pack/course/${courseId}/assessments/${key}`
    const [loaded, setLoaded] = useState<{ endpoint: string; data: AssessmentDetail | null } | null>(null)
    const isCurrent = loaded?.endpoint === endpoint
    const assessment = isCurrent ? loaded.data : null
    const loadFailed = isCurrent && loaded.data === null

    useEffect(() => {
        let isCancelled = false
        api.get<AssessmentDetail>(endpoint)
            .then((res) => { if (!isCancelled) setLoaded({ endpoint, data: res.data }) })
            .catch(() => { if (!isCancelled) setLoaded({ endpoint, data: null }) })
        return () => { isCancelled = true }
    }, [endpoint])

    const handleSaved = (next: AssessmentDetail): void => {
        setLoaded({ endpoint, data: next })
        void fetchOverview(courseId)
    }

    const backLink = (
        <Button asChild variant="ghost" className="-ml-2 min-h-11 lg:min-h-9 gap-1.5 text-muted-foreground hover:text-foreground hover:bg-primary/10">
            <Link to={coursePath(courseId)}>
                <ArrowLeft className="size-4 shrink-0" />
                <span className="truncate">{courseTitle ?? 'Back to course'}</span>
            </Link>
        </Button>
    )

    if (loadFailed) {
        return (
            <div className="max-w-lg mx-auto mt-10 p-6 sm:p-8 rounded-xl bg-card border border-border text-center space-y-4">
                <h1 className="text-lg font-bold text-foreground">Couldn't load this assignment</h1>
                <p className="text-sm text-muted-foreground">Check your connection and try again.</p>
                {backLink}
            </div>
        )
    }

    if (!assessment) {
        return (
            <div className="max-w-5xl mx-auto space-y-5" aria-busy="true">
                <Skeleton className="h-28 w-full rounded-xl" />
                <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_22rem]">
                    <Skeleton className="h-96 w-full rounded-xl" />
                    <Skeleton className="h-96 w-full rounded-xl" />
                </div>
            </div>
        )
    }

    const submission = assessment.submission
    const isReviewed = Boolean(submission?.reviewedAt)
    const Icon = assessment.kind === 'capstone' ? GraduationCap : FlaskConical

    return (
        <div className="max-w-5xl mx-auto space-y-5">
            <header className="overflow-hidden rounded-xl border border-teal/20 bg-gradient-to-br from-teal/[0.08] via-card to-primary/[0.06] shadow-xs px-3 sm:px-5 pt-2.5 pb-4 sm:pb-5 space-y-2">
                {backLink}
                <div className="px-1 flex flex-col sm:flex-row sm:items-end justify-between gap-3">
                    <div className="space-y-1 min-w-0">
                        <p className="flex flex-wrap items-center gap-x-1.5 text-[11px] font-semibold uppercase tracking-wider text-teal">
                            <Icon className="size-3.5" aria-hidden="true" />
                            {assessmentLabel(assessment)}
                            <span aria-hidden="true">·</span>
                            Due week <span className="font-mono">{assessment.weekDue}</span>
                            {assessment.covers && (
                                <span className="normal-case tracking-normal font-medium text-muted-foreground">· Covers {assessment.covers.toLowerCase()}</span>
                            )}
                        </p>
                        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">{assessment.title}</h1>
                    </div>
                    <p className={cn(
                        'shrink-0 self-start sm:self-auto inline-flex items-center gap-1.5 h-8 px-3 rounded-full border text-xs font-medium',
                        submission ? 'bg-success/10 border-success/30 text-success' : 'bg-card border-border text-muted-foreground'
                    )}>
                        {isReviewed ? <ClipboardCheck className="size-3.5" /> : submission ? <CheckCircle2 className="size-3.5" /> : <FileText className="size-3.5" />}
                        {isReviewed ? 'Reviewed' : submission ? `Submitted ${formatDate(submission.submittedAt)}` : 'Not submitted yet'}
                    </p>
                </div>
            </header>

            <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_22rem] items-start">
                <article className="rounded-xl bg-card border border-border shadow-xs px-5 py-6 sm:px-8 sm:py-7 min-w-0">
                    <ReactMarkdown remarkPlugins={[remarkGfm]} components={READING_COMPONENTS}>
                        {assessment.instructionsMarkdown}
                    </ReactMarkdown>
                </article>

                <section aria-labelledby="submission-heading" className="lg:sticky lg:top-0 rounded-xl bg-card border border-border shadow-xs p-4 sm:p-5 space-y-4">
                    <div className="space-y-1">
                        <h2 id="submission-heading" className="text-base font-bold text-foreground">
                            {isReviewed ? 'Your reviewed submission' : submission ? 'Your submission' : 'Submit your work'}
                        </h2>
                        <p className="text-xs text-muted-foreground">
                            {isReviewed
                                ? 'An evaluator has marked this. It can no longer be changed.'
                                : 'Evaluators mark it with a checklist. You can update it until it is reviewed.'}
                        </p>
                        {submission?.fileUrl && (
                            <a
                                href={resolveMediaUrl(submission.fileUrl)}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1.5 text-xs font-medium text-teal underline underline-offset-2 hover:no-underline"
                            >
                                <Paperclip className="size-3.5" />
                                {submission.fileName ?? 'Attached file'}
                            </a>
                        )}
                    </div>
                    {isReviewed ? (
                        <ReviewedSubmission assessment={assessment} />
                    ) : (
                        <SubmissionForm key={submission?.submittedAt ?? 'new'} courseId={courseId} assessment={assessment} onSaved={handleSaved} />
                    )}
                </section>
            </div>
        </div>
    )
}

export default AssessmentPage
