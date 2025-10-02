import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, ArrowLeft, Shield, Check } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { toast } from 'sonner';
import { verifySignupOtp, resendSignupOtp } from '../services/authService';
import { Loading } from './ui/loading';


export function ConfirmOtpForSignup() {
  const navigate = useNavigate();
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [countdown, setCountdown] = useState(1);
  const [canResend, setCanResend] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);

  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    // Get email data from localStorage
    const storedEmail = localStorage.getItem('signupEmail');

    if (storedEmail) {
      setEmail(storedEmail);
    } else {
      // If no pending signup found, redirect back to signup
      toast.error('No pending signup found');
      navigate('/login');
      return;
    }
  }, [navigate]);

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    } else {
      setCanResend(true);
    }
  }, [countdown]);

  useEffect(() => {
    // Auto-focus first input when component mounts
    if (inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, []);

  const handleOtpChange = (index: number, value: string) => {
    if (value.length > 1) return;

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    // Auto-focus next input
    if (value && index < 5 && inputRefs.current[index + 1]) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text/plain').replace(/\D/g, '');
    const newOtp = [...otp];

    for (let i = 0; i < Math.min(pastedData.length, 6); i++) {
      newOtp[i] = pastedData[i];
    }

    setOtp(newOtp);

    // Focus the last filled input or next empty one
    const nextIndex = Math.min(pastedData.length, 5);
    inputRefs.current[nextIndex]?.focus();
  };

  const handleVerifyOtp = async () => {
    const otpString = otp.join('');

    if (otpString.length !== 6) {
      toast.error('Please enter the complete 6-digit code');
      return;
    }

    setIsVerifying(true);

    try {
      // Call the API to verify OTP and complete signup
      await verifySignupOtp({ otp_code: otpString, email });

      // Clear localStorage after successful verification
      localStorage.removeItem('signupEmail');

      toast.success('Account created successfully!');
      navigate('/login');
    } catch (error) {
      console.error('OTP verification failed:', error);
      toast.error('Invalid verification code. Please try again.');
      setOtp(['', '', '', '', '', '']);
      if (inputRefs.current[0]) {
        inputRefs.current[0].focus();
      }
    } finally {
      setIsVerifying(false);
    }
  };

  const handleResendOtp = async () => {
    try {
      setIsLoading(true);

      const res = await resendSignupOtp({ email });

      console.log("OTP resent successfully");
      console.log("Current resend count:", res.resend_count);
      toast.success(res.message || 'Verification code resent successfully');

      // Reset countdown
      setCountdown(1);
      setCanResend(false);
    } catch (error: any) {
      // Handle specific backend errors
      if (error.message.includes("Resend limit reached")) {
        toast.error("Resend limit reached. Please restart the signup process.");
        localStorage.removeItem('signupEmail');
        navigate("/login");
      } else if (error.message.includes("OTP token not found")) {
        toast.error("OTP token not found or expired. Redirecting to signup...");
        localStorage.removeItem('signupEmail');
        navigate("/login");
      } else {
        console.error("Error resending OTP:", error);
        toast.error("Failed to resend OTP. Please try again later.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancelSignup = () => {
    // Clear localStorage when canceling
    localStorage.removeItem('signupEmail');
    navigate('/login');
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Don't render if no email data found
  if (!email) {
    return null;
  }

  if (isLoading) {
    return (<div className='border-2 border-black min-h-screen flex items-center justify-center'>
      <Loading />
    </div> // show loading spinner while fetching
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="bg-gradient-to-r from-green-600 to-green-500 p-3 rounded-full">
              <Mail className="h-8 w-8 text-white" />
            </div>
          </div>
          <h2 className="text-3xl text-gray-900">Verify Your Email</h2>
          <p className="mt-2 text-gray-600">
            Enter the 6-digit code sent to {email}
          </p>
        </div>

        <Card className="shadow-xl border-green-100">
          <CardHeader className="space-y-1">
            <CardTitle className="text-center flex items-center justify-center gap-2">
              <Shield className="h-5 w-5" />
              Email Verification
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="space-y-2">
                <Label>Verification Code</Label>
                <div className="flex gap-2 justify-center">
                  {otp.map((digit, index) => (
                    <Input
                      key={index}
                      ref={(el) => {
                        inputRefs.current[index] = el;
                      }}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      onChange={(e) => handleOtpChange(index, e.target.value)}
                      onKeyDown={(e) => handleKeyDown(index, e)}
                      onPaste={index === 0 ? handlePaste : undefined}
                      className="w-12 h-12 text-center border-green-200 focus:border-green-500"
                    />
                  ))}
                </div>
                <p className="text-xs text-gray-500 text-center">
                  Enter the 6-digit code we sent to your email
                </p>
              </div>

              <div className="text-center">
                {!canResend ? (
                  <p className="text-sm text-gray-600">
                    Resend code in {formatTime(countdown)}
                  </p>
                ) : (
                  <button
                    onClick={handleResendOtp}
                    className="text-sm text-green-600 hover:text-green-500"
                  >
                    Didn't receive the code? Resend
                  </button>
                )}
              </div>

              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={handleCancelSignup}
                  className="flex-1"
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Cancel
                </Button>
                <Button
                  onClick={handleVerifyOtp}
                  disabled={otp.join('').length !== 6 || isVerifying}
                  className="flex-1 bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600"
                >
                  {isVerifying ? (
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Verifying...
                    </div>
                  ) : (
                    <>
                      <Check className="h-4 w-4 mr-2" />
                      Verify & Sign Up
                    </>
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}