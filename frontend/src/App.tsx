import { useState, useEffect } from 'react';
import { Routes, Route, useLocation, Navigate } from 'react-router-dom'; // Import routing hooks and components
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics'; // Import the Analytics page component
import ProductionOrders from './pages/ProductionOrders';
import LoginPage from './pages/LoginPage';
import ProtectedRoute from './auth/ProtectedRoute';
import { useAuth } from './auth/AuthContext';

const MainLayout = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(false);
  const location = useLocation();

  // Function to determine the page title based on the current path
  const getPageTitle = (pathname: string): string => {
    switch (pathname) {
      case '/dashboard':
        return 'Dashboard';
      case '/analytics':
        return 'Analytics & Reporting';
      // Add cases for other pages as you create them
      case '/production-orders':
        return 'Production Orders';
      case '/job-log':        
        return 'Job Log';
      case '/schedule':        
        return 'Schedule';        
      case '/machines':
        return 'Machines Configuration';
      case '/processes':
        return 'Process Steps Configuration';
      case '/downtime-events':
        return 'Downtime Events Management';
      case '/users':
        return 'User Administration';
      default:
        return 'DigiFlow App';
    }
  };
  const [currentPageTitle, setCurrentPageTitle] = useState<string>(getPageTitle(location.pathname));

  useEffect(() => {
    setCurrentPageTitle(getPageTitle(location.pathname));
  }, [location.pathname]);

  const toggleSidebar = (): void => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="flex min-h-screen bg-backgroundLight">
      {isSidebarOpen && <div className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden" onClick={toggleSidebar}></div>}
      <div className={`fixed inset-y-0 left-0 z-50 transform ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} md:relative md:translate-x-0 transition-transform duration-300 ease-in-out`}>
        <Sidebar currentPath={location.pathname} onNavLinkClick={toggleSidebar} />
      </div>
      <div className="flex-1 flex flex-col h-screen">
        <TopBar pageTitle={currentPageTitle} onMenuToggle={toggleSidebar} />
        <main className="flex-1 p-4 md:p-6 overflow-auto">
          {/* The protected routes are now inside the MainLayout */}
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/production-orders" element={<ProductionOrders />} />
            {/* ... other protected routes */}
            <Route path="*" element={<Navigate to="/dashboard" />} />
          </Routes>
        </main>
      </div>
    </div>
  );

}

function App() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      {/* Publicly accessible login route */}
      <Route path='/login' element={<LoginPage />} />

      {/* All other protected routes */}
      <Route 
        path='/*' 
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      />  
    </Routes>
  );
}

export default App;