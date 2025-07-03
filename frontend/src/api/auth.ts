import apiClient from "./axios";

export const getCurrentUser = async() => {
  const response = await apiClient.get('/api/whoami');
  return response.data; // contains { id, email, is_admin }
}