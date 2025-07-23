import { useState } from 'react';
import { Routes, Route, useLocation, Navigate } from 'react-router-dom';
import { useAuth } from './auth/AuthContext';
import ProtectedRoute from './auth/ProtectedRoute';

/* --- Layout Components --- */
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';

/* --- Page Imports --- */
// Admin Pages
import Dashboard from './pages/Admin/Dashboard';
import Analytics from './pages/Admin/Analytics';
import ProductionOrders from './pages/Admin/ProductionOrders';
import LoginPage from './pages/Admin/LoginPage';
import Machines from './pages/Admin/Machines';
import ProcessSteps from './pages/Admin/ProcessSteps';
import DowntimeEvents from './pages/Admin/DowntimeEvents';
import SchedulePage from './pages/Admin/Schedule';
import JobLogsPage from './pages/Admin/JobLog';
import UsersPage from './pages/Admin/Users';

// Operator Pages
import OperatorLogin from './pages/Operator/OperatorLogin';
import MachineSelectPage from './pages/Operator/MachineSelect';
import MachineTaskPage from './pages/Operator/MachineTask';
import { Toaster } from 'react-hot-toast';

/**
 * MainLayout is the shell for the entire authenticated ADMIN experience.
 * It includes the sidebar and top bar.
 */
const MainLayout = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(false);
  const location = useLocation();

  const getPageTitle = (pathname: string): string => {
    const path = pathname.split('/').pop()?.replace('-', ' ') || 'Dashboard';
    return path.charAt(0).toUpperCase() + path.slice(1);
  };

  const toggleSidebar = (): void => setIsSidebarOpen(!isSidebarOpen);

  return (
    <>
      <Toaster
        position='top-right'
        toastOptions={{
          success: {
            style: {
              background: '#22c55e',
              color: 'white',
            },
          },
          error: {
            style: {
              background: '#ef4444',
              color: 'white',
            },
          },
        }}
      />
      <div className="flex min-h-screen bg-gray-100">
        <div className={`fixed inset-y-0 left-0 z-50 transform ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} md:relative md:translate-x-0 transition-transform duration-300 ease-in-out`}>
          <Sidebar currentPath={location.pathname} onNavLinkClick={() => setIsSidebarOpen(false)} />
        </div>
        <div className="flex-1 flex flex-col h-screen">
          <TopBar pageTitle={getPageTitle(location.pathname)} onMenuToggle={toggleSidebar} />
          <main className="flex-1 p-4 md:p-6 overflow-auto">
            <Routes>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/production-orders" element={<ProductionOrders />} />
              <Route path='/schedule' element={<SchedulePage />} />
              <Route path='/job-log' element={<JobLogsPage />} />
              <Route path='/machines' element={<Machines />} />
              <Route path='/processes' element={<ProcessSteps />} />
              <Route path='/downtime-events' element={<DowntimeEvents />} />
              <Route path='/users' element={<UsersPage />} />
              {/* Redirect any other admin path to dashboard */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </>
  );
};

/**
 * The main App component now acts as a top-level router,
 * directing users based on their authentication status and role.
 */
function App() {
  const { isAuthenticated, userRole } = useAuth();

  return (
    <Routes>
      {/* --- Public Routes --- */}
      {/* These routes are accessible to everyone. */}
      <Route path="/login" element={!isAuthenticated ? <LoginPage /> : <Navigate to="/dashboard" />} />
      <Route path="/operator/login" element={!isAuthenticated ? <OperatorLogin /> : <Navigate to="/operator/select-machine" />} />

      {/* --- Protected Routes --- */}
      {/* The "/*" path catches all other routes. The ProtectedRoute component will handle redirection. */}
      <Route 
        path="/*" 
        element={
          <ProtectedRoute>
            <>
              {/* Once authenticated, we check the role to render the correct UI */}
              {(userRole === 'admin' || userRole === 'manager') && <MainLayout />}
              
              {userRole === 'operator' && (
                <Routes>
                  <Route path="/operator/select-machine" element={<MachineSelectPage />} />
                  <Route path="/operator/task/:machineIdCode" element={<MachineTaskPage />} />
                  
                  {/* Any other operator path redirects to machine selection */}
                  <Route path="*" element={<Navigate to="/operator/select-machine" replace />} />
                </Routes>
              )}
            </>
          </ProtectedRoute>
        } 
      />
    </Routes>
  );
}

export default App;