import { createContext, useState, useContext, useEffect, type ReactNode } from 'react';
import { jwtDecode } from 'jwt-decode'; // You'll need to install this: npm install jwt-decode

// Define the shape of the context data, now including userRole
interface AuthContextType {
  isAuthenticated: boolean;
  userRole: string | null;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('accessToken'));
  const [userRole, setUserRole] = useState<string | null>(null);

  // This effect runs when the component mounts or the token changes
  useEffect(() => {
    const storedToken = localStorage.getItem('accessToken');
    if (storedToken) {
      try {
        // Decode the token to extract the role payload
        const decoded: { role: string } = jwtDecode(storedToken);
        setToken(storedToken);
        setUserRole(decoded.role);
      } catch (error) {
        console.error("Invalid token found in storage:", error);
        logout(); // Clear out the invalid token
      }
    }
  }, []);

  const login = (newToken: string) => {
    try {
      const decoded: { role: string } = jwtDecode(newToken);
      setToken(newToken);
      setUserRole(decoded.role); // Set the role on login
      localStorage.setItem('accessToken', newToken);
    } catch (error) {
      console.error("Failed to decode token on login:", error);
    }
  };

  const logout = () => {
    setToken(null);
    setUserRole(null); // Clear the role on logout
    localStorage.removeItem('accessToken');
    // A full page reload to /login ensures all state is cleared
    window.location.href = '/login';
  };

  const isAuthenticated = !!token;

  return (
    <AuthContext.Provider value={{ isAuthenticated, userRole, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};