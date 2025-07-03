import React, { createContext, useState, useContext, useEffect } from 'react'
import type { ReactNode } from 'react'

interface AuthContextType {
  isAuthenticated: boolean;
  login: (token: string) => void; // Function to log in, takes a string token
  logout: () => void; // Function to log out, takes no arguments
}

// Create the context with a default value It's typed as AuthContextType | undefined because it will be undefined initially before the Provider's value is set. The `useAuth` hook handles the `undefined` check.
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Define the props for the AuthProvider component
interface AuthProviderProps {
  children: ReactNode; // `ReactNode` is the correct type for children in React
}

// Create the provider component React.FC<AuthProviderProps> explicitly types this functional component
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  // State to hold the authentication token. It attempts to get the token from localStorage on initial render. Type is `string | null` because the token can either be a string or null (if not logged in).
  const [token, setToken] = useState<string | null>(localStorage.getItem('accessToken'));

  // useEffect hook to handle initial token check from local storage. This ensures the token state is correctly initialized if a token exists from a previous session.
  useEffect(() => {
    const storedToken = localStorage.getItem('accessToken');
    if (storedToken) {
      setToken(storedToken);
    }
  }, []); // Empty dependency array means this effect runs only once after the initial render.

  // `login` function: updates the token state and stores it in localStorage.
  const login = (newToken: string) => {
    setToken(newToken);
    localStorage.setItem('accessToken', newToken);
  };

  // `logout` function: clears the token state and removes it from localStorage.
  const logout = () => {
    setToken(null);
    localStorage.removeItem('accessToken');
    window.location.href = '/login';
  };

  // `isAuthenticated` derived state: true if a token exists, false otherwise. The `!!` (double negation) converts a truthy/falsy value (string/null) into a boolean.
  const isAuthenticated = !!token;

  return (
    // The AuthContext.Provider makes the `value` available to all components wrapped by it.
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// Create a custom hook for easy access to the context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
