import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { toast } from "sonner";
import { setIsAuthenticated, setUser, setLoading } from "./redux/slices/authSlice";
import { getUserById, getUserDetails } from "./services/profileService";
import { RootState } from "./redux/store"; // adjust import if needed

function AppInitializer() {
    const dispatch = useDispatch();

    // Get userId from slice
    const currentUserId = useSelector((state: RootState) => state.auth.user?.id);

    useEffect(() => {
        const initializeAuth = async () => {
            dispatch(setLoading(true));
            
            try {
                const userData = await getUserDetails();

                if (userData.id !== currentUserId) {
                    dispatch(setUser({ id: userData.id, profile_pic_url: userData.profile_pic_url }));
                }
                dispatch(setIsAuthenticated(true));
            } catch (error) {
                dispatch(setUser(null));
                dispatch(setIsAuthenticated(false));
                // toast.error("Failed to fetch user. Please log in again.");
            } finally {
                dispatch(setLoading(false));
            }
        };

        initializeAuth();
    }, []); // still safe here, since `dispatch` is stable


    return null; // this component does not render anything
}

export default AppInitializer;
