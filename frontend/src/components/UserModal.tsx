import React, { useState, useEffect } from 'react';
import { type UserData, type UserUpdateInput } from '../types/users'; // Adjust the path to your user type
import { toast } from 'react-toastify';

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: any) => void;
  initialData?: Partial<UserData>;
  isEditing?: boolean;
};

type ModalProps = {
    isOpen: boolean;
    onClose: () => void;
    title?: string;
    children: React.ReactNode;
};

const Modal: React.FC<ModalProps> = ({
    isOpen, onClose, title, children
}) => {
    if(!isOpen) return null;
    return (
        <div className='fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center'>
            <div className='bg-white p-6 rounded shadow-lg w-[400px] max-w-full'>
                {title && <h2 className='text-lg font-semibold mb-4'>{title}</h2>}
                {children}
                <div className='mt-4 text-right'>
                    <button onClick={onClose} className='text-sm text-gray-600 hover:text-gray-900'>Close</button>
                </div>
            </div>
        </div>
    );
};

const UserModal: React.FC<Props> = ({ isOpen, onClose, onSave, initialData, isEditing = false }) => {
  const defaultFormState = {
    username: '',
    full_name: '',
    email: '',
    password: '',
    role: 'user',
    is_superuser: false,
    is_active: true,
  }

  const [formState, setFormState] = useState(defaultFormState);

  useEffect(() => {
    if (!isOpen) return;

    if (isEditing && initialData) {
      setFormState({
        ...defaultFormState,
        ...initialData,
        password: '',
      });
    } else {
      setFormState(defaultFormState)
    }
  }, [isOpen, isEditing, initialData]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const newValue =
      type === 'checkbox' && e.target instanceof HTMLInputElement
        ? e.target.checked
        : value;
    setFormState((prev) => ({
      ...prev,
      [name]: newValue,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const updates: Partial<typeof formState> = { ...formState };
    if (isEditing) delete updates.password;
    if (!isEditing && !formState.password) {
      toast.error('Password is required for new users.');
      return;
    }
    if (isEditing && formState.password === '') {
      delete updates.password;
    }
    console.log("PATCH PAYLOAD ->", formState)
    onSave(updates);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={isEditing ? 'Edit User' : 'Add New User'}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input name="username" value={formState.username} onChange={handleChange} placeholder="Username" className="input" required />
        <input name="full_name" value={formState.full_name} onChange={handleChange} placeholder="Full Name" className="input" />
        <input name="email" type="email" value={formState.email} onChange={handleChange} placeholder="Email" className="input" required />
        <input name="password" type="password" value={formState.password} onChange={handleChange} placeholder="Password" className="input" required={!isEditing} />
        <select name="role" value={formState.role} onChange={handleChange} className="input">
          <option value="user">User</option>
          <option value="operator">Operator</option>
          <option value="admin">Admin</option>
        </select>
        <label className="flex items-center space-x-2">
          <input type="checkbox" name="is_superuser" checked={formState.is_superuser} onChange={handleChange} />
          <span>Superuser</span>
        </label>
        <label className="flex items-center space-x-2">
          <input type="checkbox" name="is_active" checked={formState.is_active} onChange={handleChange} />
          <span>Active</span>
        </label>

        <div className="flex justify-end space-x-3 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
          <button type="submit" className="btn-primary">{isEditing ? 'Update' : 'Add'}</button>
        </div>
      </form>
    </Modal>
  );
};

export default UserModal;
