import React from 'react';
import { Link } from 'react-router-dom'; // Import Link from react-router-dom
import { useAuth } from '../auth/AuthContext';
import { getCurrentUser } from '../api/auth';
import { useQuery } from '@tanstack/react-query';

// Define props for Sidebar
interface SidebarProps {
    currentPath: string; // To determine which link is active
    onNavLinkClick: () => void; // To close sidebar on mobile after clicking a link
}

const Sidebar: React.FC<SidebarProps> = ({ currentPath, onNavLinkClick }) => {
    // Helper function to determine if a link is active
    const isActive = (path: string) => currentPath === path;
    const {logout} = useAuth()
    const { data: user, isLoading, isError } = useQuery({
        queryKey: ['whoami'],
        queryFn: getCurrentUser,
        staleTime: 5*60*1000,
    });

    return (
        <div className="flex flex-col h-screen w-64 bg-sidebarDark text-textLight shadow-lg">
            {/* Logo Section */}
            <div className="flex items-center justify-center h-20 bg-gray-800 border-b border-gray-700">
            <img
                src="images/digiflow.svg"
                alt="DigiFlow Logo"
                className="h-10 w-auto rounded"
            />
            </div>

            {/* Navigation Sections */}
            <nav className="flex-1 px-4 py-6 overflow-y-auto">
            {/* Primary Views */}
            <div className="mb-6">
                <h3 className="text-xs font-semibold uppercase text-gray-400 mb-3 px-2">Primary Views</h3>
                <ul>
                <li className="mb-2">
                    <Link
                    to="/dashboard" // Use Link for navigation
                    onClick={onNavLinkClick} // Close sidebar on click
                    className={`flex items-center px-2 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                        isActive('/dashboard') ? 'text-primaryBlue bg-gray-700' : 'text-gray-300 hover:bg-gray-700 hover:text-primaryBlue'
                    }`}
                    >
                    {/* Dashboard Icon */}
                    <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1H11m-4 0a1 1 0 001 1h2m-4-2h4"></path></svg>
                    Dashboard
                    </Link>
                </li>
                <li className="mb-2">
                    <Link
                    to="/analytics" // Use Link for navigation
                    onClick={onNavLinkClick}
                    className={`flex items-center px-2 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                        isActive('/analytics') ? 'text-primaryBlue bg-gray-700' : 'text-gray-300 hover:bg-gray-700 hover:text-primaryBlue'
                    }`}
                    >
                    {/* Analytics Icon */}
                    <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"></path></svg>
                    Analytics
                    </Link>
                </li>
                </ul>
            </div>

            {/* Operations */}
            <div className="mb-6">
                <h3 className="text-xs font-semibold uppercase text-gray-400 mb-3 px-2">Operations</h3>
                <ul>
                <li className="mb-2">
                    <Link
                    to="/production-orders"
                    onClick={onNavLinkClick}
                    className={`flex items-center px-2 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                        isActive('/production-orders') ? 'text-primaryBlue bg-gray-700' : 'text-gray-300 hover:bg-gray-700 hover:text-primaryBlue'
                    }`}
                    >
                    {/* Production Orders Icon */}
                    <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M17 16l4-4m-4 4l-4-4"></path></svg>
                    Production Orders
                    </Link>
                </li>
                <li className="mb-2">
                    <Link
                    to="/job-log"
                    onClick={onNavLinkClick}
                    className={`flex items-center px-2 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                        isActive('/job-log') ? 'text-primaryBlue bg-gray-700' : 'text-gray-300 hover:bg-gray-700 hover:text-primaryBlue'
                    }`}
                    >
                    {/* Job Log Icon */}
                    <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9h2m-2 4h2m2-4h2m-2 4h2m-6-4h.01M17 16l4-4m-4 4l-4-4"></path></svg>
                    Job Log
                    </Link>
                </li>
                <li className="mb-2">
                    <Link
                    to="/schedule"
                    onClick={onNavLinkClick}
                    className={`flex items-center px-2 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                        isActive('/schedule') ? 'text-primaryBlue bg-gray-700' : 'text-gray-300 hover:bg-gray-700 hover:text-primaryBlue'
                    }`}
                    >
                    {/* Job Log Icon */}
                    <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9h2m-2 4h2m2-4h2m-2 4h2m-6-4h.01M17 16l4-4m-4 4l-4-4"></path></svg>
                    Schedule
                    </Link>
                </li>            
                </ul>
            </div>

            {/* Configuration */}
            <div className="mb-6">
                <h3 className="text-xs font-semibold uppercase text-gray-400 mb-3 px-2">Configuration</h3>
                <ul>
                <li className="mb-2">
                    <Link
                    to="/machines"
                    onClick={onNavLinkClick}
                    className={`flex items-center px-2 py-2 rounded-lg text-sm font-medium text-gray-300 hover:bg-gray-700 hover:text-primaryBlue transition-colors duration-200 ${
                        isActive('/machines') ? 'text-primaryBlue bg-gray-700' : 'text-gray-300 hover:bg-gray-700 hover:text-primaryBlue'
                    }`}
                    >
                    {/* Machines Icon */}
                    <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.525-.322 1.01-.81 1.066-2.572z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                    Machines
                    </Link>
                </li>
                <li className="mb-2">
                    <Link
                    to="/processes"
                    onClick={onNavLinkClick}
                    className={`flex items-center px-2 py-2 rounded-lg text-sm font-medium text-gray-300 hover:bg-gray-700 hover:text-primaryBlue transition-colors duration-200 ${
                        isActive('/processes') ? 'text-primaryBlue bg-gray-700' : 'text-gray-300 hover:bg-gray-700 hover:text-primaryBlue'
                    }`}
                    >
                    {/* Processes Icon */}
                    <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v2a2 2 0 01-2 2H5a2 2 0 01-2-2v-2a2 2 0 012-2m14 0V9a2 2 0 00-2-2H5a2 2 0 00-2 2v2m7-8v2m0 4v2m0 4v2m-6-4v2m6-4v2m6-4v2"></path></svg>
                    Processes
                    </Link>
                </li>
                <li className="mb-2">
                    <Link
                    to="/downtime-events"
                    onClick={onNavLinkClick}
                    className={`flex items-center px-2 py-2 rounded-lg text-sm font-medium text-gray-300 hover:bg-gray-700 hover:text-primaryBlue transition-colors duration-200 ${
                        isActive('/downtime-events') ? 'text-primaryBlue bg-gray-700' : 'text-gray-300 hover:bg-gray-700 hover:text-primaryBlue'
                    }`}
                    >
                    {/* Downtime Events Icon */}
                    <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                    Downtime Events
                    </Link>
                </li>
                </ul>
            </div>

            {/* Administration */}
            <div className="mb-6">
                <h3 className="text-xs font-semibold uppercase text-gray-400 mb-3 px-2">Administration</h3>
                <ul>
                <li className="mb-2">
                    <Link
                    to="/users"
                    onClick={onNavLinkClick}
                    className={`flex items-center px-2 py-2 rounded-lg text-sm font-medium text-gray-300 hover:bg-gray-700 hover:text-primaryBlue transition-colors duration-200 ${
                        isActive('/users') ? 'text-primaryBlue bg-gray-700' : 'text-gray-300 hover:bg-gray-700 hover:text-primaryBlue'
                    }`}
                    >
                    {/* Users Icon */}
                    <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H2v-2a3 3 0 015.356-1.857M17 20v-2c0-.653-.146-1.286-.421-1.857M7 20v-2c0-.653.146-1.286.421-1.857M12 10a6 6 0 100-12 6 6 0 000 12zm-2 1a2 2 0 114 0 2 2 0 01-4 0z"></path></svg>
                    Users
                    </Link>
                </li>
                </ul>
            </div>
            </nav>

            {/* User Profile at the bottom */}
            <div className="px-4 py-4 border-t border-gray-700 flex items-center justify-between">
            <div className="flex items-center">
                <img
                src="https://placehold.co/40x40/6B7280/FFFFFF?text=JD"
                alt="User Avatar"
                className="w-10 h-10 rounded-full mr-3 border-2 border-primaryBlue"
                />
                <div>
                    {isLoading ? (
                        <p className="text-sm text-gray-400">Loading...</p>
                    ) : isError || !user ? (
                        <p className="text-sm text-red-400">User not found</p>
                    ) : (
                        <>
                        <p className="text-sm font-semibold text-textLight">
                            {user.email}
                        </p>
                        <p className="text-xs text-gray-400">
                            {user.is_admin ? 'Admin' : 'User'}
                        </p>
                        </>
                    )}
                </div>
            </div>
            {/* Logout/Settings Icon */}
            <button onClick={logout} className='text-gray-400 hover:text-primaryBlue transition-colors duration-200' title='Logout'>
                <svg className='w-5 h-5' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                    <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1' />
                </svg>
            </button>
            </div>
        </div>
    );
};

export default Sidebar;