import { apiGet } from '@/lib/apiClient'
import type { DashboardMetrics } from '@/types'

export const dashboardService = {
  metrics: () => apiGet<DashboardMetrics>('/dashboard/metrics'),
}
