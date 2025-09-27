import { createSlice, createAsyncThunk, PayloadAction } from "@reduxjs/toolkit";

import { login, logout, refreshAccessToken, sendOtp, signup } from "../../services/authService";

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

// Async thunk for login
export const loginUser = createAsyncThunk(
    "auth/loginUser",
    async ({ email, password }: { email: string; password: string }, { rejectWithValue }) => {
        try {
            const response = await login(email, password);
            return response.user; // return the user object for Redux state
        } catch (err: any) {
            return rejectWithValue(err.response?.data?.message || "Login failed");
        }
    }
);

// Async thunk for signup (triggers OTP send)
export const signupUser = createAsyncThunk(
    "auth/signupUser",
    async (formData: any, { rejectWithValue }) => {
        try {
            const response = await signup(formData);
            return response.message; // just return message instead of user object
        } catch (err: any) {
            return rejectWithValue(err.response?.data?.message || "Signup failed");
        }
    }
);

// redux/slices/authSlice.ts
export const sendOtpUser = createAsyncThunk(
    "auth/sendOtpUser",
    async (email: string, { rejectWithValue }) => {
        try {
            const response = await sendOtp(email); // service function
            return response.message; // e.g., "OTP sent successfully"
        } catch (err: any) {
            return rejectWithValue(err.response?.data?.message || "Failed to send OTP");
        }
    }
);

export const refreshTokenThunk = createAsyncThunk(
    "auth/refreshToken",
    async (_, { rejectWithValue }) => {
        try {
            const res = await refreshAccessToken();
            return res.accessToken;
        } catch (err: any) {
            return rejectWithValue(err.response?.data || "Failed to refresh token");
        }
    }
);


export const logoutThunk = createAsyncThunk(
    "auth/logout",
    async (_, { rejectWithValue }) => {
        try {
            const res = await logout(); // call backend logout
            return res; // optional: can return message if needed
        } catch (err: any) {
            return rejectWithValue(err.response?.data || "Failed to logout");
        }
    }
);

export const authSlice = createSlice({
    name: "auth",
    initialState,
    reducers: {
        logout: (state) => {
            state.loading = false;
            state.isAuthenticated = false;
            state.user = null;
        }
    },
    extraReducers: (builder) => {
        builder
            // Login
            .addCase(loginUser.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(loginUser.fulfilled, (state, action: PayloadAction<User>) => {
                state.loading = false;
                state.user = action.payload;
                state.isAuthenticated = true;
            })
            .addCase(loginUser.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })

            // refreshTokenThunk pending → optional: set loading state
            .addCase(refreshTokenThunk.pending, (state) => {
                state.loading = true;
            })
            // refreshTokenThunk fulfilled → update auth state if needed
            .addCase(refreshTokenThunk.fulfilled, (state, action) => {
                state.loading = false;
                state.isAuthenticated = true;
            })
            // refreshTokenThunk rejected → mark user as logged out
            .addCase(refreshTokenThunk.rejected, (state) => {
                state.loading = false;
                state.isAuthenticated = false;
                state.user = null;
            })

            // SignUp
            .addCase(signupUser.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(signupUser.fulfilled, (state, action: PayloadAction<User>) => {
                state.loading = false;
                state.isAuthenticated = true;
            })
            .addCase(signupUser.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })

            // logout
            .addCase(logoutThunk.pending, (state) => {
                state.loading = true;
            })
            .addCase(logoutThunk.fulfilled, (state) => {
                state.loading = false;
                state.isAuthenticated = false;
                state.user = null;
            })
            .addCase(logoutThunk.rejected, (state) => {
                state.loading = false;
            });
    },
});

// Named export for reducer
export default authSlice.reducer;
