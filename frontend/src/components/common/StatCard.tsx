import type { LucideIcon } from 'lucide-react'
import { Card } from './Card'
import clsx from 'clsx'

export function StatCard({
  label,
  value,
  icon: Icon,
  tone = 'blue',
  hint,
}: {
  label: string
  value: string | number
  icon: LucideIcon
  tone?: 'blue' | 'green' | 'amber' | 'purple'
  hint?: string
}) {
  const toneClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-emerald-50 text-emerald-600',
    amber: 'bg-amber-50 text-amber-600',
    purple: 'bg-purple-50 text-purple-600',
  }[tone]

  return (
    <Card className="p-4 sm:p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-500">{label}</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
          {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
        </div>
        <div className={clsx('rounded-lg p-2.5', toneClasses)}>
          <Icon size={20} />
        </div>
      </div>
    </Card>
  )
}
