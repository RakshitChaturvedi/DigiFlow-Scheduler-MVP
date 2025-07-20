import apiClient from  './axios'

export interface DowntimeByReason {
    reason: string;
    count: number;
}

export interface OrderStatusSummary {
    status: string;
    count: number;
}

export interface AnalyticsData {
    downtime_by_reason: DowntimeByReason[],
    order_status_summary: OrderStatusSummary[],
}

// Fetch aggregated data for analytics dashboard.
export const getAnalyticsData = async (): Promise<AnalyticsData> => {
    const response = await apiClient.get('/api/analytics/summary');
    return response.data;
}