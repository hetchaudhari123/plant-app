import { createSlice, PayloadAction } from "@reduxjs/toolkit";

// Define the user type 
interface User {
    id: string;
}

// Define the auth state
interface AuthState {
    user: User | null;
    isAuthenticated: boolean;
    loading: boolean;
    error: string | null;
}

const initialState: AuthState = {
    user: null,
    isAuthenticated: false,
    loading: false,
    error: null,
};

export const authSlice = createSlice({
    name: "auth",
    initialState,
    reducers: {
        setLoading: (state, action: PayloadAction<boolean>) => {
            state.loading = action.payload;
        },
        setUser: (state, action: PayloadAction<User | null>) => {
            state.user = action.payload;
            state.isAuthenticated = action.payload !== null;
        },
        setIsAuthenticated: (state, action: PayloadAction<boolean>) => {
            state.isAuthenticated = action.payload;
        },
        setError: (state, action: PayloadAction<string | null>) => {
            state.error = action.payload;
        },
        logout: (state) => {
            state.loading = false;
            state.isAuthenticated = false;
            state.user = null;
            state.error = null;
        },
    },
});

// Named exports for synchronous actions
export const { setLoading, setUser, setError, logout, setIsAuthenticated } = authSlice.actions;

// Default export for reducer
export default authSlice.reducer;
