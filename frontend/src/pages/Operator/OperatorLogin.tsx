import React from 'react';
import { useForm, type SubmitHandler } from 'react-hook-form';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';
import apiClient from '../../api/axios';
import toast from 'react-hot-toast'; // Assuming you have react-hot-toast installed

// Define the shape of the form data
interface LoginFormData {
  username: string; // This will hold the email
  password: string;
}

// Define the shape of the API response
interface LoginResponse {
  access_token: string;
  token_type: string;
}

// Define the API function that sends data in the correct format
const loginOperator = async (credentials: LoginFormData): Promise<LoginResponse> => {
  const params = new URLSearchParams();
  // Your backend's OAuth2PasswordRequestForm expects 'username' and 'password' fields
  params.append('username', credentials.username);
  params.append('password', credentials.password);

  const response = await apiClient.post('/api/user/login', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return response.data;
};

const OperatorLogin: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth(); // Use the login function from our context
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<LoginFormData>();

  const loginMutation = useMutation({
    mutationFn: loginOperator,
    onSuccess: (data) => {
      // The login function from the context handles storing the token and updating the auth state
      login(data.access_token);
      // The navigation is now handled by the main App component based on the user's role
      // We no longer navigate directly from here.
      // navigate('/operator/select-machine'); // This line is removed
    },
    onError: () => {
      toast.error("Login failed. Please check your username and password.");
    },
  });

  const onSubmit: SubmitHandler<LoginFormData> = (data) => {
    loginMutation.mutate(data);
  };

  return (
    <div className='min-h-screen bg-gray-100 flex items-center justify-center px-4'>
      <form 
        onSubmit={handleSubmit(onSubmit)} 
        className='bg-white p-6 rounded-lg shadow-lg w-full max-w-sm'
      >
        <h1 className='text-2xl font-bold mb-6 text-center text-gray-800'>DigiFlow Operator Login</h1>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Username / Email</label>
          <input
            type='text'
            {...register("username", { required: "Username is required" })}
            placeholder='Enter your username or email'
            className='w-full p-3 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500'
          />
          {errors.username && <p className="text-red-500 text-sm mt-1">{errors.username.message}</p>}
        </div>

        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input
            type='password'
            {...register("password", { required: "Password is required" })}
            placeholder='Enter your password'
            className='w-full p-3 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500'
          />
          {errors.password && <p className="text-red-500 text-sm mt-1">{errors.password.message}</p>}
        </div>

        <button
          type='submit'
          disabled={isSubmitting}
          className='w-full bg-blue-600 text-white py-3 rounded hover:bg-blue-700 mt-6 disabled:bg-blue-400 transition-colors'
        >
          {isSubmitting ? "Logging in..." : "Login"}
        </button>
      </form>
    </div>
  );
};

export default OperatorLogin;