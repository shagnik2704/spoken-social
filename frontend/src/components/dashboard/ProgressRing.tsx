interface ProgressRingProps {
    percent: number
    size?: number
    strokeWidth?: number
    label?: string
    children?: React.ReactNode
}

export const ProgressRing: React.FC<ProgressRingProps> = ({ percent, size = 72, strokeWidth = 7, label, children }) => {
    const clamped = Math.min(100, Math.max(0, percent))
    const radius = (size - strokeWidth) / 2
    const circumference = 2 * Math.PI * radius
    const offset = circumference * (1 - clamped / 100)
    const isComplete = clamped >= 100

    return (
        <div
            className="relative shrink-0"
            style={{ width: size, height: size }}
            role="img"
            aria-label={label ?? `${clamped}% complete`}
        >
            <svg width={size} height={size} className="-rotate-90">
                <circle cx={size / 2} cy={size / 2} r={radius} fill="none" strokeWidth={strokeWidth} className="stroke-muted" />
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    fill="none"
                    strokeWidth={strokeWidth}
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    className={`transition-[stroke-dashoffset] duration-700 ease-out ${isComplete ? 'stroke-success' : 'stroke-primary'}`}
                />
            </svg>
            <span className="absolute inset-0 flex items-center justify-center font-mono text-sm font-bold text-foreground">
                {children ?? `${clamped}%`}
            </span>
        </div>
    )
}
