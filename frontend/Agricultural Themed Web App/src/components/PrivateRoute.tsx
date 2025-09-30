import React, { ReactNode } from "react";
import { useSelector } from "react-redux";
import { Navigate, useLocation } from "react-router-dom";
import { RootState } from "../redux/store";

interface PrivateRouteProps {
  children: ReactNode;
}

const PrivateRoute: React.FC<PrivateRouteProps> = ({ children }) => {
  const { isAuthenticated, loading } = useSelector(
    (state: RootState) => state.auth
  );
  const location = useLocation();

  // If not authenticated and not loading, redirect to login
  if (!isAuthenticated && !loading) {
    // Save intended route so we can redirect after login
    localStorage.setItem(
      "redirectAfterLogin",
      location.pathname + location.search
    );
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default PrivateRoute;
