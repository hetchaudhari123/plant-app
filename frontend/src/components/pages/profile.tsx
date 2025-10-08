import { useEffect, useState } from 'react';
import { User, Settings, Shield, Edit3, Save, X, Mail, Pencil, EyeOff, Eye, Lock, AlertTriangle, Trash2 } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { createOtpToken, deleteUser, getUserDashboardMetrics, getUserDetails, getUserPrimaryCrops, requestEmailUpdateOtp, updateFarmSize, updateUserAvatar, updateUserName } from '../../services/profileService';
import { toast } from "sonner";
import { useNavigate } from 'react-router-dom';
import { changePassword, logoutUser } from '../../services/authService';
import { logout } from '../../redux/slices/authSlice';
import { useDispatch } from 'react-redux';
import { AxiosError } from "axios";

export interface UserProfile {
  firstName: string;
  lastName: string;
  email: string;
  farmSize: FarmSize | "";  // allow empty string initially
  cropTypes: string[];
  avatar: string;
}

export type FarmSize =
  | "1-5 acres"
  | "5-20 acres"
  | "20-50 acres"
  | "50-100 acres"
  | "100+ acres";


export function Profile() {
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState<boolean>(true); // loading state
  const [showChangeEmailForm, setShowChangeEmailForm] = useState(false);
  const [newEmail, setNewEmail] = useState('');

  const [profile, setProfile] = useState<UserProfile>({
    firstName: '',
    lastName: '',
    email: '',
    farmSize: '',
    cropTypes: [],
    avatar: ''
  });

  const [avatarFile, setAvatarFile] = useState<File | null>(null);



  const [metrics, setMetrics] = useState({
    totalAnalyses: 0,
    issuesDetected: 0,
    cropsMonitored: [] as string[],
    healthyCrops: 0,
  });
  const [editedProfile, setEditedProfile] = useState<UserProfile>(profile);
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showChangePasswordForm, setShowChangePasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [showDeleteAccountForm, setShowDeleteAccountForm] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  const [deletePassword, setDeletePassword] = useState('');
  const [showDeletePassword, setShowDeletePassword] = useState(false);
  const handleDeleteAccount = async () => {
    if (deleteConfirmation !== 'DELETE') {
      toast.error("Please type DELETE to confirm");
      return;
    }

    if (!deletePassword) {
      toast.error("Please enter your password");
      return;
    }

    try {
      await deleteUser({ password: deletePassword });

      toast.success("Account deleted successfully");
      localStorage.clear();
      navigate('/');

    }
    catch (error: unknown) {
      console.error("Error deleting account:", error);

      let message = "Incorrect password or failed to delete account";

      if (error instanceof AxiosError) {
        // Explicitly type the response data
        const data = error.response?.data as { message?: string } | undefined;

        if (data?.message) {
          message = data.message;
        } else if (error.message) {
          message = error.message;
        }
      } else if (error instanceof Error) {
        message = error.message;
      }

      toast.error(message);
    }
  };
  const handleChangePassword = async () => {
    // Validate passwords match
    if (newPassword !== confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    // Validate all fields are filled
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error("Please fill in all fields");
      return;
    }

    try {
      await changePassword({
        old_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword
      });

      // Close form and reset fields
      setShowChangePasswordForm(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setShowCurrentPassword(false);
      setShowNewPassword(false);
      setShowConfirmPassword(false);

      toast.success("Password changed successfully! Please log in with your new password.");

      // Log out user and redirect to login
      setTimeout(async () => {
        try {
          await logoutUser();
          // Clear any local storage storage if needed
          localStorage.clear();
          navigate('/login');
        } catch (error) {
          console.error("Logout API failed...", error);
        }
      }, 1500);

    } catch (error: unknown) {
      console.error("Error changing password:", error);

      let message = "Failed to change password. Please try again.";

      if (error instanceof AxiosError) {
        // Safely access the backend message
        message = error.response?.data?.message || message;
      } else if (error instanceof Error) {
        message = error.message || message;
      }

      toast.error(message);
    }
  };

  const fetchProfile = async () => {
    try {
      const userData = await getUserDetails(); // API call
      const cropsData = await getUserPrimaryCrops(); // returns string[] of crop names

      setProfile({
        firstName: userData.first_name,
        lastName: userData.last_name,
        email: userData.email,
        farmSize: userData.farm_size as FarmSize, // cast to enum type
        cropTypes: cropsData || [],
        avatar: userData.profile_pic_url || ''
      });
      setEditedProfile({
        firstName: userData.first_name,
        lastName: userData.last_name,
        email: userData.email,
        farmSize: userData.farm_size as FarmSize, // cast to enum type
        cropTypes: cropsData || [],
        avatar: userData.profile_pic_url || ''
      }); // initialize editedProfile here, after data is fetched

      const metricsData = await getUserDashboardMetrics();
      setMetrics({
        totalAnalyses: metricsData.total_analyses,
        issuesDetected: metricsData.issues_detected,
        cropsMonitored: metricsData.crops_monitored,
        healthyCrops: metricsData.healthy_crops,
      });
    } catch (error) {
      console.error("Failed to fetch profile:", error);
    } finally {
      setIsLoading(false); // done loading
    }
  };
  useEffect(() => {

    fetchProfile();
  }, []); // empty dependency array → runs once on mount





  const handleInputChange = (field: keyof UserProfile, value: string) => {
    setEditedProfile(prev => ({ ...prev, [field]: value }));
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAvatarFile(file);
      // Optionally, show preview locally before saving
      setProfile((prev) => ({
        ...prev,
        avatar: URL.createObjectURL(file) // temporary preview
      }));
    }
  };


  const handleSave = async () => {
    setIsLoading(true); // Start loading
    try {
      // --- Name update ---
      if (editedProfile.firstName !== profile.firstName || editedProfile.lastName !== profile.lastName) {
        await updateUserName({
          firstName: editedProfile.firstName,
          lastName: editedProfile.lastName
        });
      }

      // --- Avatar upload ---
      if (avatarFile) {
        const response = await updateUserAvatar(avatarFile);
        editedProfile.avatar = response.new_pic_url; // update URL from backend
        setAvatarFile(null); // clear temporary file
      }

      // --- Farm size update ---
      if (editedProfile.farmSize !== profile.farmSize) {
        await updateFarmSize(editedProfile.farmSize);
      }

      // --- Refresh profile data from server ---
      await fetchProfile();

      // --- Update UI state after successful save ---
      setIsEditing(false);
      toast.success("Profile updated successfully!");

    } catch (error) {
      console.error("Failed to save profile:", error);
      toast.error("Failed to save changes. Please try again.");
      setIsLoading(false); // Set loading false on error since fetchProfile won't run
    }
  };


  const handleCancel = () => {
    setEditedProfile(profile);
    setIsEditing(false);
  };


  const handleEmailChange = async () => {
    // Validate inputs
    if (!password) {
      toast.error('Please enter your password');
      return;
    }

    if (!newEmail) {
      toast.error('Please enter your new email address');
      return;
    }
    setIsLoading(true); // start loading before request
    try {
      // Call the API function
      await requestEmailUpdateOtp({
        new_email: newEmail,
        current_password: password
      });

      await createOtpToken(profile.email, newEmail)

      // Store the new email in localStorage for use in confirm-email-change
      localStorage.setItem('pendingNewEmail', newEmail);
      localStorage.setItem('oldEmail', profile.email);

      console.log('Email change OTP requested for:', profile.email, 'to:', newEmail);
      toast.success('Verification code sent to your current email');

      // Reset form state
      setPassword('');
      setNewEmail('');
      setShowPassword(false);
      setShowChangeEmailForm(false);

      // Navigate to email change confirmation page
      navigate('/confirm-email-change');

    } catch (error) {
      console.error('Failed to request email change OTP:', error);
      toast.error('Failed to send verification code. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  const dispatch = useDispatch();
  const handleSignOut = async () => {

    try {

      // Call backend logout
      await logoutUser();

      // Clear local storage
      localStorage.clear();
      dispatch(logout());
      // Navigate to login page
      navigate("/login");
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };


  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl text-gray-900">Profile</h1>
          <p className="text-gray-600">Manage your account settings and preferences</p>
        </div>

        <div className="flex gap-2 items-center">
          {!isEditing ? (
            <Button
              onClick={() => setIsEditing(true)}
              className="bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600"
            >
              <Edit3 className="h-4 w-4 mr-2" />
              Edit Profile
            </Button>
          ) : (
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleCancel}>
                <X className="h-4 w-4 mr-2" />
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                disabled={isLoading}
                className="bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Changes
                  </>
                )}
              </Button>
            </div>
          )}

          {/* Sign Out Button */}
          <Button
            variant="outline"
            onClick={handleSignOut}
            className="ml-2 text-red-600 border-red-600 hover:bg-red-50"
          >
            Sign Out
          </Button>
        </div>
      </div>


      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Card */}
        <div className="lg:col-span-1">
          <Card className="border-green-100">
            <CardContent className="p-6 text-center">
              <div className="relative inline-block mb-4 group">
                <div className="relative w-24 h-24 rounded-full overflow-hidden">
                  {/* Image */}
                  {profile.avatar ? (
                    <img
                      src={profile.avatar}
                      alt="Profile"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    // Fallback
                    <div className="w-full h-full bg-green-100 text-green-700 text-2xl flex items-center justify-center">
                      {profile.firstName[0]}
                      {profile.lastName[0]}
                    </div>
                  )}

                  {isEditing && (
                    <>
                      <input
                        type="file"
                        id="avatar-upload"
                        className="hidden"
                        accept="image/*"
                        onChange={handleFileSelect}
                      />
                      <label
                        htmlFor="avatar-upload"
                        className="absolute inset-0 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 cursor-pointer bg-gradient-to-b from-black/50 to-black/80"
                      >
                        <Pencil className="h-8 w-8 text-green-700" />
                      </label>
                    </>
                  )}
                </div>
              </div>

              <h2 className="text-xl text-gray-900">
                {profile.firstName} {profile.lastName}
              </h2>
              <p className="text-gray-600 mb-4">{profile.email}</p>



              <div className="mt-4">
                <Badge className="bg-green-100 text-green-800">Verified Farmer</Badge>
              </div>
            </CardContent>
          </Card>

          {/* Stats Card */}
          <Card className="border-green-100 mt-6">
            <CardHeader>
              <CardTitle className="text-lg">Farm Statistics</CardTitle>
            </CardHeader>
            <CardContent className="p-6 pt-0">
              <div className="grid grid-cols-2 gap-4">
                {[
                  { label: "Total Analyses", value: metrics.totalAnalyses },
                  { label: "Issues Detected", value: metrics.issuesDetected },
                  { label: "Crops Monitored", value: metrics.cropsMonitored ?? 0 },
                  { label: "Healthy Crops", value: metrics.healthyCrops ?? 0 }
                ].map((stat, index) => (
                  <div key={index} className="text-center">
                    <div className="text-2xl text-green-600 mb-1">{stat.value}</div>
                    <div className="text-xs text-gray-600">{stat.label}</div>
                  </div>
                ))
                }
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Personal Information */}
          <Card className="border-green-100">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Personal Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="firstName">First Name</Label>
                  <Input
                    id="firstName"
                    value={isEditing ? editedProfile.firstName : profile.firstName}
                    onChange={(e) => handleInputChange('firstName', e.target.value)}
                    disabled={!isEditing}
                    className="border-green-200 focus:border-green-500"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lastName">Last Name</Label>
                  <Input
                    id="lastName"
                    value={isEditing ? editedProfile.lastName : profile.lastName}
                    onChange={(e) => handleInputChange('lastName', e.target.value)}
                    disabled={!isEditing}
                    className="border-green-200 focus:border-green-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="email"
                      type="email"
                      value={profile.email}
                      disabled={true}
                      className="pl-10 border-green-200 focus:border-green-500"
                    />
                  </div>
                </div>

              </div>


            </CardContent>
          </Card>

          {/* Farm Information */}
          <Card className="border-green-100">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Farm Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="farmSize">Farm Size</Label>
                  <Select
                    value={isEditing ? editedProfile.farmSize : profile.farmSize}
                    onValueChange={(value: string) => handleInputChange('farmSize', value)}
                    disabled={!isEditing}
                  >
                    <SelectTrigger className="border-green-200">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1-5 acres">1-5 acres</SelectItem>
                      <SelectItem value="5-20 acres">5-20 acres</SelectItem>
                      <SelectItem value="20-50 acres">20-50 acres</SelectItem>
                      <SelectItem value="50-100 acres">50-100 acres</SelectItem>
                      <SelectItem value="100+ acres">100+ acres</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Primary Crops</Label>
                  <div className="flex flex-wrap gap-2 p-3 border border-green-200 rounded-md min-h-[42px]">
                    {profile.cropTypes.map((crop, index) => (
                      <Badge key={index} variant="secondary" className="bg-green-100 text-green-800">
                        {crop}

                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>



          {/* Security */}
          <Card className="border-green-100">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Security
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Button
                  variant="outline"
                  className="w-full border-green-200 hover:bg-green-50"
                  onClick={() => setShowChangePasswordForm(true)}
                >
                  <Lock className="h-4 w-4 mr-2" />
                  Change Password
                </Button>

                {showChangePasswordForm && (
                  <div className="space-y-4 p-6 border border-green-200 rounded-lg bg-white shadow-sm mt-4">
                    <div className="space-y-2">
                      <h3 className="text-lg font-semibold">Change Password</h3>
                      <p className="text-sm text-gray-600">
                        Update your password to keep your account secure.
                      </p>
                    </div>

                    <div className="space-y-4">
                      <div className="space-y-2">
                        <p className="text-sm text-gray-600">
                          Please enter your current password and choose a new password.
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="currentPasswordChange">Current Password</Label>
                        <div className="relative">
                          <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                          <Input
                            id="currentPasswordChange"
                            type={showCurrentPassword ? 'text' : 'password'}
                            placeholder="Enter your current password"
                            value={currentPassword}
                            onChange={(e) => setCurrentPassword(e.target.value)}
                            className="pl-10 pr-10 border-green-200 focus:border-green-500"
                          />
                          <button
                            type="button"
                            onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                            className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                          >
                            {showCurrentPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </button>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="newPassword">New Password</Label>
                        <div className="relative">
                          <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                          <Input
                            id="newPassword"
                            type={showNewPassword ? 'text' : 'password'}
                            placeholder="Enter your new password"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            className="pl-10 pr-10 border-green-200 focus:border-green-500"
                          />
                          <button
                            type="button"
                            onClick={() => setShowNewPassword(!showNewPassword)}
                            className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                          >
                            {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </button>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="confirmPassword">Confirm New Password</Label>
                        <div className="relative">
                          <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                          <Input
                            id="confirmPassword"
                            type={showConfirmPassword ? 'text' : 'password'}
                            placeholder="Confirm your new password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            className="pl-10 pr-10 border-green-200 focus:border-green-500"
                          />
                          <button
                            type="button"
                            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                            className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                          >
                            {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </button>
                        </div>
                      </div>

                      <div className="flex gap-3 justify-end">
                        <Button
                          variant="outline"
                          onClick={() => {
                            setShowChangePasswordForm(false);
                            setCurrentPassword('');
                            setNewPassword('');
                            setConfirmPassword('');
                            setShowCurrentPassword(false);
                            setShowNewPassword(false);
                            setShowConfirmPassword(false);
                          }}
                        >
                          Cancel
                        </Button>
                        <Button
                          onClick={handleChangePassword}
                          disabled={!currentPassword || !newPassword || !confirmPassword || newPassword !== confirmPassword}
                          className="bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600"
                        >
                          Change Password
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {showChangeEmailForm ? (
                <div className="space-y-4 p-6 border border-green-200 rounded-lg bg-white shadow-sm">
                  <div className="space-y-2">
                    <h3 className="text-lg font-semibold">Change Email Address</h3>
                    <p className="text-sm text-gray-600">
                      Update your profile information and settings here.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div className="space-y-2">
                      <p className="text-sm text-gray-600">
                        To change your email address, please enter your current password for security verification.
                      </p>
                      <p className="text-sm text-gray-600">
                        Current email: <span className="font-medium">{profile.email}</span>
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="newEmail">New Email Address</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="newEmail"
                          type="email"
                          placeholder="Enter your new email address"
                          value={newEmail}
                          onChange={(e) => setNewEmail(e.target.value)}
                          className="pl-10 border-green-200 focus:border-green-500"
                          disabled={isLoading}
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="currentPassword">Current Password</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="currentPassword"
                          type={showPassword ? 'text' : 'password'}
                          placeholder="Enter your current password"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          className="pl-10 pr-10 border-green-200 focus:border-green-500"
                          disabled={isLoading}
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                          disabled={isLoading}
                        >
                          {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                    </div>

                    <div className="flex gap-3 justify-end">
                      <Button
                        variant="outline"
                        onClick={() => {
                          setShowChangeEmailForm(false);
                          setPassword('');
                          setNewEmail('');
                          setShowPassword(false);
                        }}
                        disabled={isLoading}
                      >
                        Cancel
                      </Button>
                      <Button
                        onClick={handleEmailChange}
                        className="bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600"
                        disabled={isLoading}
                      >
                        {isLoading ? 'Sending Email...' : 'Continue'}
                      </Button>
                    </div>
                  </div>
                </div>
              ) : (
                <Button
                  variant="outline"
                  className="w-full border-green-200 hover:bg-green-50"
                  onClick={() => setShowChangeEmailForm(true)}
                >
                  <Mail className="h-4 w-4 mr-2" />
                  Change Email
                </Button>
              )}


              {showDeleteAccountForm ? (
                <div className="space-y-4 p-6 border border-red-200 rounded-lg bg-red-50 shadow-sm">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5 text-red-600" />
                      <h3 className="text-lg font-semibold text-red-900">Delete Account</h3>
                    </div>
                    <p className="text-sm text-red-800">
                      This action is permanent and cannot be undone. All your data will be permanently deleted.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div className="bg-white p-4 rounded border border-red-200">
                      <p className="text-sm font-medium text-gray-900 mb-2">
                        You will lose access to:
                      </p>
                      <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
                        <li>All your profile data and settings</li>
                        <li>Your order history and saved items</li>
                        <li>Any active subscriptions or credits</li>
                        <li>Access to all associated services</li>
                      </ul>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="confirmDelete" className="text-red-900">
                        Type <span className="font-mono font-bold">DELETE</span> to confirm
                      </Label>
                      <Input
                        id="confirmDelete"
                        type="text"
                        placeholder="Type DELETE to confirm"
                        value={deleteConfirmation}
                        onChange={(e) => setDeleteConfirmation(e.target.value)}
                        className="border-red-300 focus:border-red-500"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="deletePassword" className="text-red-900">
                        Enter your password to confirm
                      </Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="deletePassword"
                          type={showDeletePassword ? 'text' : 'password'}
                          placeholder="Enter your password"
                          value={deletePassword}
                          onChange={(e) => setDeletePassword(e.target.value)}
                          className="pl-10 pr-10 border-red-300 focus:border-red-500"
                        />
                        <button
                          type="button"
                          onClick={() => setShowDeletePassword(!showDeletePassword)}
                          className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                        >
                          {showDeletePassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                    </div>

                    <div className="flex gap-3 justify-end">
                      <Button
                        variant="outline"
                        onClick={() => {
                          setShowDeleteAccountForm(false);
                          setDeleteConfirmation('');
                          setDeletePassword('');
                          setShowDeletePassword(false);
                        }}
                      >
                        Cancel
                      </Button>
                      <Button
                        onClick={handleDeleteAccount}
                        disabled={deleteConfirmation !== 'DELETE' || !deletePassword}
                        className="bg-red-600 hover:bg-red-700 text-white"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete Account Permanently
                      </Button>
                    </div>
                  </div>
                </div>
              ) : (
                <Button
                  variant="outline"
                  className="w-full border-red-200 hover:bg-red-50 text-red-600"
                  onClick={() => setShowDeleteAccountForm(true)}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Account
                </Button>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div >
  );
}