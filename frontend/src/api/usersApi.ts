import axios from "axios";
import apiClient from "./axios";
import { type UserData, type UserCreateInput, type UserUpdateInput, type ResetPasswordInput, type SelfUpdateInput } from "../types/users";

export const getUsers = async (): Promise<UserData[]> => {
    const response = await apiClient.get('/api/admin/users');
    console.log("fetched users: ", response.data);
    return response.data;
};

// Fetch single user
export const getUserById = async (id:string): Promise<UserData> => {
    const response = await apiClient.get(`/api/admin/users/${id}`);
    return response.data;
}

// Update user
export const updateUser = async ({
    id,
    updates,
}: {
    id: string; 
    updates: UserUpdateInput
}): Promise<UserData> => {
    const response = await apiClient.patch(`/api/admin/users/${id}`, updates);
    return response.data;
};

// Create user
export const createUser = async (newUser: UserCreateInput): Promise<UserData> => {
    const response = await apiClient.post('/api/admin/users', newUser);
    return response.data;
};

// Delete User
export const deleteUser = async (id: string): Promise<void> => {
    await apiClient.delete(`/api/admin/users/${id}`);
};

// Reset user password
export const resetUserPassword = async (id: string, newPassword: string) => {
    const response = await apiClient.patch(`/api/admin/users/${id}`, {password: newPassword});
    return response.data;
}