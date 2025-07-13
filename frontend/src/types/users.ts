export interface UserData {
    id: string;
    username: string;
    email: string;
    full_name?: string;
    is_active: boolean;
    is_superuser: boolean;
    role: string;
}

export interface UserCreateInput {
    username: string;
    email: string;
    full_name?: string;
    is_active?: boolean;
    is_superuser?: boolean;
    role?: string;
}

export interface UserUpdateInput {
    email?: string;
    full_name?: string;
    username?: string;
    password?: string;
    is_active?: boolean;
    is_superuser?: boolean;
    role?: string;
}

export interface SelfUpdateInput {
    full_name?: string;
    email?: string;
    username?: string;
}

export interface ResetPasswordInput {
    id: string;
    newPassword: string;
}