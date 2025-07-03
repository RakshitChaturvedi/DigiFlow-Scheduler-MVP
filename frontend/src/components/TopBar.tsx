import React from "react";

interface TopBarProps{
    pageTitle: string; // Title of current page to display
    onMenuToggle: () => void; // Function to call when the mobile menu button is clicked
}

const TopBar: React.FC<TopBarProps> = ({ pageTitle, onMenuToggle }) => {
    return (
        <header className="bg-white shadow-sm h-16 flex items-center justify-between px-4 md:px-6 z-30">
            {/* Mobile Menu Button */}
            <button className="md:hidden p-2 rounded-md text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primaryBlue"
                onClick={onMenuToggle} // Connect to the passed onMenuToggle prop
            >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
            </button>

            <h1 className="text-xl font-semibold text-textDark">{pageTitle}</h1>  {/* Dynamic Page Title */}
            <div className="flex items-center space-x-4">
                {/* Notification Bell */}
                <button className="p-2 rounded-full text-gray-700 hover:bg-gray-100 focus:outline-none focus:right-2 focus:ring-inset focus:ring-primaryBlue">
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.403 5.353 6 7.917 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />                        
                    </svg>
                </button>

                {/* User Profile Dropdown */}
                <div className="relative">
                    <button className="flex items-center space-x-2 text-gray-700 hover:text-primaryBlue focus:outline-none">
                        <img src="https://placehold.co/32x32/6B7280/FFFFFF?text=U" // Placeholder for user avatar
                            alt="User Avatar"
                            className="w-8 h-8 rounded-full border border-borderColor"
                        />
                        <span className="hidden md:block text-sm font-medium">John Doe</span>
                        <svg className="w-4 h-4 hidden md:block" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 91-7 7-7-7" />
                        </svg>
                    </button>
                    {/* dropdown content hidden for now */}
                </div>
            </div>
        </header>
    );
};

export default TopBar