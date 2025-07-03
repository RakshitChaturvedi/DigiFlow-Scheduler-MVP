import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

interface ProtectedRouteProps {
    children: React.ReactElement;
}

const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
    const {isAuthenticated} = useAuth();

    if (!isAuthenticated) {
        return <Navigate to="/login" />;
    }

    return children; // User is authenticated, render the children components
};

export default ProtectedRoute