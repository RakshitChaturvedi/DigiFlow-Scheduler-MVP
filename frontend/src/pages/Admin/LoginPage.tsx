import React, {useState} from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext.tsx';
import apiClient from '../../api/axios.ts'; 

// Define the shape of login response
interface LoginResponse {
    access_token: string;
    token_type: string;
}

interface LoginRequest {
    email: string;
    password: string;
}

// Define the API function for logging in
const loginUser = async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post('/api/user/login', credentials, {
        headers: { 'Content-Type': 'application/json' },
    });
    return response.data;
};

// The Login Form Component
function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const { login } = useAuth();

  const loginMutation = useMutation({
    mutationFn: loginUser,
    onSuccess: (data) => {
      // On successful login, call the login function from our context
      login(data.access_token);
      // And navigate to the main dashboard
      navigate('/dashboard');
    },
    onError: (error) => {
      // TanStack Query automatically provides the error object
      console.error('Login failed:', error);
    },
  });

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    loginMutation.mutate({email, password});
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-sm p-8 space-y-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-center text-gray-800">Welcome Back</h2>
      
      {loginMutation.isError && (
        <div className="p-3 text-sm text-red-700 bg-red-100 rounded-lg" role="alert">
          Invalid email or password. Please try again.
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700">Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700">Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
      <button 
        type="submit" 
        disabled={loginMutation.isPending}
        className="w-full px-4 py-2 font-semibold text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-blue-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        {loginMutation.isPending ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}

// The login Page component (which centers the form)
export default function LoginPage() {
    return (
        <div className='flex items-center justify-center min-h-screen bg-gray-100'>
            <LoginForm />
        </div>
    )
}