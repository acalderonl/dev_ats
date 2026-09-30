import clsx from 'clsx'
import type { HTMLAttributes } from 'react'

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('rounded-xl border border-slate-200 bg-white shadow-sm', className)} {...props} />
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('flex items-center justify-between border-b border-slate-100 px-4 py-3 sm:px-5', className)} {...props} />
}

export function CardBody({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('p-4 sm:p-5', className)} {...props} />
}
