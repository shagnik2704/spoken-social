import { createElement } from 'react'
import { BarChart3, Brain, Code, Compass, Database, FileText, FlaskConical, Settings, Sparkles, Terminal, type LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

const COURSE_ICONS: Record<string, LucideIcon> = {
    'Python': Code,
    'Linux': Terminal,
    'Scilab': BarChart3,
    'C/C++': Settings,
    'LibreOffice': FileText,
    'PostgreSQL': Database,
    'AI': Brain,
    'PHD': FlaskConical,
    'Developing Empathy and Growth Mindset': Compass,
    'Personality and Human Development': Compass,
    'Being Creative with AI': Sparkles,
    'Interactive AI Tools': Brain,
}

interface CourseIconProps {
    title: string
    className?: string
}

export const CourseIcon: React.FC<CourseIconProps> = ({ title, className }) => {
    const icon: LucideIcon | undefined = COURSE_ICONS[title]
    return createElement(icon ?? Code, { className: cn(icon !== undefined ? 'text-primary' : 'text-muted-foreground', className), 'aria-hidden': true })
}
