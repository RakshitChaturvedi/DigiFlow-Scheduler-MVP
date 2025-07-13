import apiClient from "./axios";

export async function createSchedule(startTimeAnchor?: string) {
    const payload = startTimeAnchor ? { start_time_anchor: startTimeAnchor } : {};

    const response = await apiClient.post('api/schedule', payload);
    return response.data;
}