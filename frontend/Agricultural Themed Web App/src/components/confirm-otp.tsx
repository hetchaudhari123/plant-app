import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Leaf, ArrowLeft, RefreshCw } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { toast } from 'sonner';
import { sendOtp, signup } from '../services/authService';
import type { AppDispatch, RootState } from "../redux/store";
import { useDispatch, useSelector } from "react-redux";
import { sendOtpUser, signupUser } from '../redux/slices/authSlice';

export function ConfirmOtp() {
    const [otp, setOtp] = useState(['', '', '', '', '', '']);
    const { loading } = useSelector((state: RootState) => state.auth);
    const [timeLeft, setTimeLeft] = useState(60);
    const [canResend, setCanResend] = useState(false);
    const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
    const navigate = useNavigate();
    const dispatch = useDispatch<AppDispatch>();
    const location = useLocation();

    // Timer for resend OTP
    useEffect(() => {
        if (timeLeft > 0) {
            const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
            return () => clearTimeout(timer);
        } else {
            setCanResend(true);
        }
    }, [timeLeft]);

    const handleInputChange = (value: string, index: number) => {
        if (value.length > 1) return; // Prevent multiple characters

        const newOtp = [...otp];
        newOtp[index] = value;
        setOtp(newOtp);

        // Auto-focus next input
        if (value && index < 5) {
            inputRefs.current[index + 1]?.focus();
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
        if (e.key === 'Backspace' && !otp[index] && index > 0) {
            inputRefs.current[index - 1]?.focus();
        }
    };

    const { formData } = location.state as {
        formData: { firstName: string; lastName: string; email: string; password: string };
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const otpCode = otp.join("");

        if (otpCode.length !== 6) {
            toast.error("Please enter the complete 6-digit OTP");
            return;
        }


        try {
            // Dispatch the signup thunk with OTP
            const resultAction = await dispatch(
                signupUser({ ...formData, otp: otpCode })
            );

            if (signupUser.fulfilled.match(resultAction)) {
                console.log("Signup successful:", resultAction.payload);
                toast.success("OTP verified successfully! Account created.");
                navigate("/login"); // Redirect to login page
            } else {
                toast.error(resultAction.payload as string || "Failed to verify OTP.");
            }
        } catch (error: any) {
            console.error("OTP verification error:", error);
            toast.error(error?.message || "Failed to verify OTP. Please try again.");
        }
    };



    const handleResendOtp = async () => {

        try {
            const resultAction = await dispatch(sendOtpUser(formData.email));

            if (sendOtpUser.fulfilled.match(resultAction)) {
                console.log("Resend OTP response:", resultAction.payload);
                toast.success("OTP sent successfully!");
                setTimeLeft(60); // restart countdown
                setCanResend(false);
                setOtp(["", "", "", "", "", ""]);
                inputRefs.current[0]?.focus();
            } else {
                toast.error(resultAction.payload as string || "Failed to resend OTP.");
                setTimeLeft(0);    // allow immediate retry
                setCanResend(true);
            }
        } catch (error: any) {
            console.error("Resend OTP failed:", error);
            toast.error(error?.message || "Failed to resend OTP. Please try again.");
        }
    };


    return (
        <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-md w-full space-y-8">
                <div className="text-center">
                    <div className="flex justify-center mb-4">
                        <div className="bg-gradient-to-r from-green-600 to-green-500 p-3 rounded-full">
                            <Leaf className="h-8 w-8 text-white" />
                        </div>
                    </div>
                    <h2 className="text-3xl text-gray-900">
                        Verify Your Account
                    </h2>
                    <p className="mt-2 text-gray-600">
                        We've sent a 6-digit verification code to your email address
                    </p>
                </div>

                <Card className="shadow-xl border-green-100">
                    <CardHeader className="space-y-1">
                        <CardTitle className="text-center">
                            Enter Verification Code
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleSubmit} className="space-y-6">
                            <div className="flex justify-between space-x-2">
                                {otp.map((digit, index) => (
                                    <input
                                        key={index}
                                        ref={(el) => {
                                            inputRefs.current[index] = el;
                                        }}
                                        type="text"
                                        maxLength={1}
                                        value={digit}
                                        onChange={(e) => handleInputChange(e.target.value, index)}
                                        onKeyDown={(e) => handleKeyDown(e, index)}
                                        className="w-12 h-12 text-center border-2 border-green-200 rounded-lg focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-200 transition-colors"
                                        autoComplete="off"
                                    />
                                ))}
                            </div>

                            <Button
                                type="submit"
                                disabled={loading || otp.some(digit => !digit)}
                                className="w-full bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600 shadow-md disabled:opacity-50"
                            >
                                {loading ? (
                                    <>
                                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                                        Verifying...
                                    </>
                                ) : (
                                    'Verify OTP'
                                )}
                            </Button>
                        </form>

                        <div className="mt-6 text-center">
                            <p className="text-sm text-gray-600 mb-4">
                                Didn't receive the code?
                            </p>

                            {canResend ? (
                                <Button
                                    variant="outline"
                                    onClick={handleResendOtp}
                                    disabled={loading}
                                    className="border-green-200 hover:bg-green-50"
                                >
                                    {loading ? (
                                        <>
                                            <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                                            Sending...
                                        </>
                                    ) : (
                                        'Resend OTP'
                                    )}
                                </Button>
                            ) : (
                                <p className="text-sm text-gray-500">
                                    Resend available in {timeLeft}s
                                </p>
                            )}
                        </div>

                        <div className="mt-6 text-center">
                            <Link
                                to="/login"
                                className="inline-flex items-center text-sm text-green-600 hover:text-green-500"
                            >
                                <ArrowLeft className="h-4 w-4 mr-1" />
                                Back to login
                            </Link>
                        </div>
                    </CardContent>
                </Card>

                <div className="text-center">
                    <p className="text-xs text-gray-500">
                        For testing purposes, use OTP: <span className="font-mono bg-gray-100 px-2 py-1 rounded">123456</span>
                    </p>
                </div>
            </div>
        </div>
    );
}