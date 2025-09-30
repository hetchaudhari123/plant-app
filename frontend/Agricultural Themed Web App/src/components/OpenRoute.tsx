import React, { ReactNode } from "react";
import { useSelector } from 'react-redux';
import { Navigate } from 'react-router-dom';
import type { RootState } from "../redux/store";

interface OpenRouteProps {
  children: ReactNode;
}

const OpenRoute: React.FC<OpenRouteProps> = ({ children }) => {
    const { isAuthenticated } = useSelector((state: RootState) => state.auth);
    if (!isAuthenticated) {
        return children; // user not logged in, allow access
    }
    // ✅ If user is logged in, check if there's a redirect path
    const redirectPath = localStorage.getItem("redirectAfterLogin") || "/";
    return <Navigate to={redirectPath} />;
};

export default OpenRoute;