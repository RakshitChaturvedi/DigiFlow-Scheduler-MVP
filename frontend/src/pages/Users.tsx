import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-toastify';
import {
  getUsers,
  getUserById,
  updateUser,
  createUser,
  deleteUser,
  resetUserPassword,
} from '../api/usersApi';
import { type UserData, type UserCreateInput, type UserUpdateInput } from '../types/users';
import UserModal from '../components/UserModal';
import { useMutation } from '@tanstack/react-query';

const UsersPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = React.useState(false);
  const [isEditing, setIsEditing] = React.useState(false);
  const [selectedUser, setSelectedUser] = React.useState<UserData | null>(null);
  const [ShowPasswordReset, setShowPasswordReset] = useState<number | null>(null);
  const [newPassword, setNewPassword] = useState('');

  const { data: users = [], isLoading, isError, error } = useQuery<UserData[], Error>({
    queryKey: ['users'],
    queryFn: getUsers,
    staleTime: 1000 * 60 * 5,
  });

  const mutationDelete = useMutation({
    mutationFn: deleteUser,
    onSuccess: () => {
      toast.success("User deleted");
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: () => toast.error("Failed to delete user"),
  });

    const mutationResetPassword = useMutation<
    any,                                 // response type
    Error,                               // error type
    { id: string; password: string }     // variables type
    >({
    mutationFn: ({ id, password }: { id: string; password: string }) => {
        return resetUserPassword(id, password);
    },
    onSuccess: () => {
        toast.success('Password reset');
        setShowPasswordReset(null);
        setNewPassword('');
    },
    onError: () => {
        toast.error('Failed to reset password');
      },
    });

  const handleAddUser = () => {
    setIsEditing(false);
    setSelectedUser(null);
    setIsModalOpen(true);
  };

  const handleEditUser = async (id: string) => {
    try {
      const user = await getUserById(id);
      setIsEditing(true);
      setSelectedUser(user);
      setIsModalOpen(true);
    } catch {
      toast.error("Failed to fetch user details");
    }
  };

  const handleDeleteUser = (id: string) => {
    if (window.confirm("Delete this user?")) {
      mutationDelete.mutate(id);
    }
  };

  const handleResetPassword = async (id: string) => {
    const newPassword = prompt("Enter new password:");
    if (newPassword && newPassword.length >= 8) {
      mutationResetPassword.mutate({ id, password: newPassword });
    } else {
      toast.warning("Password must be at least 8 characters");
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between mb-6">
        <h2 className="text-2xl font-semibold">User Management</h2>
        <button
          onClick={handleAddUser}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Add User
        </button>
      </div>

      {isLoading ? (
        <p>Loading...</p>
      ) : isError ? (
        <p className="text-red-600">{error.message}</p>
      ) : (
        <table className="w-full table-auto border-collapse">
          <thead>
            <tr className="bg-gray-100 text-sm">
              <th className="p-2 border">Username</th>
              <th className="p-2 border">Email</th>
              <th className="p-2 border">Role</th>
              <th className="p-2 border">Active</th>
              <th className="p-2 border">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user.id} className="text-sm text-center">
                <td className="p-2 border">{user.username}</td>
                <td className="p-2 border">{user.email}</td>
                <td className="p-2 border">{user.role}</td>
                <td className="p-2 border">{user.is_active ? 'Yes' : 'No'}</td>
                <td className="p-2 border space-x-2">
                  <button onClick={() => handleEditUser(user.id)} className="text-yellow-600 hover:underline">
                    Edit
                  </button>
                  <button onClick={() => handleDeleteUser(user.id)} className="text-red-600 hover:underline">
                    Delete
                  </button>
                  <button onClick={() => handleResetPassword(user.id)} className="text-blue-600 hover:underline">
                    Reset Password
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {isModalOpen && (
        <UserModal
        isOpen={isModalOpen}
        isEditing={isEditing}
        initialData={selectedUser ?? undefined}
        onClose={() => {
            setIsModalOpen(false);
            setSelectedUser(null);
            setIsEditing(false);
            queryClient.invalidateQueries({ queryKey: ['users'] });
        }}
        onSave={(data) => {
            if (isEditing && selectedUser) {
            updateUser({ id: selectedUser.id, updates: data })
                .then(() => {
                toast.success("User updated");
                queryClient.invalidateQueries({ queryKey: ['users'] });
                setIsModalOpen(false);
                })
                .catch(() => toast.error("Update failed"));
            } else {
            createUser(data)
                .then(() => {
                toast.success("User created");
                queryClient.invalidateQueries({ queryKey: ['users'] });
                setIsModalOpen(false);
                })
                .catch(() => toast.error("Create failed"));
            }
        }}
        />
      )}
    </div>
  );
};

export default UsersPage;
