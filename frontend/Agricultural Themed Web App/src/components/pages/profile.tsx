import { useState } from 'react';
import { User, Settings, Bell, Shield, Camera, Edit3, Save, X, Mail, Phone, MapPin, Calendar } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { Switch } from '../ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Separator } from '../ui/separator';
import { Badge } from '../ui/badge';

interface UserProfile {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  location: string;
  farmSize: string;
  cropTypes: string[];
  bio: string;
  avatar: string;
}

export function Profile() {
  const [isEditing, setIsEditing] = useState(false);
  const [profile, setProfile] = useState<UserProfile>({
    firstName: 'John',
    lastName: 'Smith',
    email: 'john.smith@email.com',
    phone: '+1 (555) 123-4567',
    location: 'California, USA',
    farmSize: '50 acres',
    cropTypes: ['Tomatoes', 'Corn', 'Lettuce'],
    bio: 'Passionate organic farmer with 15 years of experience in sustainable agriculture. Always looking for innovative ways to improve crop health and yield.',
    avatar: ''
  });

  const [editedProfile, setEditedProfile] = useState<UserProfile>(profile);

  const [notifications, setNotifications] = useState({
    emailAlerts: true,
    pushNotifications: true,
    weeklyReports: false,
    marketingEmails: false
  });

  const handleInputChange = (field: keyof UserProfile, value: string) => {
    setEditedProfile(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    setProfile(editedProfile);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditedProfile(profile);
    setIsEditing(false);
  };

  const cropOptions = ['Tomatoes', 'Corn', 'Lettuce', 'Peppers', 'Cucumbers', 'Carrots', 'Beans', 'Wheat', 'Rice', 'Potatoes'];

  const stats = [
    { label: 'Total Analyses', value: '47' },
    { label: 'Issues Detected', value: '12' },
    { label: 'Crops Monitored', value: '3' },
    { label: 'Success Rate', value: '94%' }
  ];

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl text-gray-900">Profile</h1>
          <p className="text-gray-600">Manage your account settings and preferences</p>
        </div>
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
              className="bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600"
            >
              <Save className="h-4 w-4 mr-2" />
              Save Changes
            </Button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Card */}
        <div className="lg:col-span-1">
          <Card className="border-green-100">
            <CardContent className="p-6 text-center">
              <div className="relative inline-block mb-4">
                <Avatar className="w-24 h-24">
                  <AvatarImage src={profile.avatar} />
                  <AvatarFallback className="bg-green-100 text-green-700 text-2xl">
                    {profile.firstName[0]}{profile.lastName[0]}
                  </AvatarFallback>
                </Avatar>
                {isEditing && (
                  <button className="absolute bottom-0 right-0 bg-green-600 hover:bg-green-700 text-white p-2 rounded-full">
                    <Camera className="h-4 w-4" />
                  </button>
                )}
              </div>
              
              <h2 className="text-xl text-gray-900">
                {profile.firstName} {profile.lastName}
              </h2>
              <p className="text-gray-600 mb-4">{profile.email}</p>
              
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-center gap-2 text-gray-600">
                  <MapPin className="h-4 w-4" />
                  <span>{profile.location}</span>
                </div>
                <div className="flex items-center justify-center gap-2 text-gray-600">
                  <Calendar className="h-4 w-4" />
                  <span>Member since Jan 2024</span>
                </div>
              </div>

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
                {stats.map((stat, index) => (
                  <div key={index} className="text-center">
                    <div className="text-2xl text-green-600 mb-1">{stat.value}</div>
                    <div className="text-xs text-gray-600">{stat.label}</div>
                  </div>
                ))}
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
                      value={isEditing ? editedProfile.email : profile.email}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      disabled={!isEditing}
                      className="pl-10 border-green-200 focus:border-green-500"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone</Label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="phone"
                      value={isEditing ? editedProfile.phone : profile.phone}
                      onChange={(e) => handleInputChange('phone', e.target.value)}
                      disabled={!isEditing}
                      className="pl-10 border-green-200 focus:border-green-500"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="location">Location</Label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="location"
                    value={isEditing ? editedProfile.location : profile.location}
                    onChange={(e) => handleInputChange('location', e.target.value)}
                    disabled={!isEditing}
                    className="pl-10 border-green-200 focus:border-green-500"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="bio">Bio</Label>
                <Textarea
                  id="bio"
                  rows={3}
                  value={isEditing ? editedProfile.bio : profile.bio}
                  onChange={(e) => handleInputChange('bio', e.target.value)}
                  disabled={!isEditing}
                  className="border-green-200 focus:border-green-500"
                />
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
                    onValueChange={(value: string)=> handleInputChange('farmSize', value)}
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
                        {isEditing && (
                          <button className="ml-1 text-green-600 hover:text-green-800">
                            <X className="h-3 w-3" />
                          </button>
                        )}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Notifications */}
          <Card className="border-green-100">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                Notification Preferences
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm">Email Alerts</p>
                    <p className="text-xs text-gray-600">Receive alerts when issues are detected</p>
                  </div>
                  <Switch
                    checked={notifications.emailAlerts}
                    onCheckedChange={(checked: boolean) => 
                      setNotifications(prev => ({ ...prev, emailAlerts: checked }))
                    }
                  />
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm">Push Notifications</p>
                    <p className="text-xs text-gray-600">Get instant notifications on your device</p>
                  </div>
                  <Switch
                    checked={notifications.pushNotifications}
                    onCheckedChange={(checked: boolean) => 
                      setNotifications(prev => ({ ...prev, pushNotifications: checked }))
                    }
                  />
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm">Weekly Reports</p>
                    <p className="text-xs text-gray-600">Receive weekly farm health summaries</p>
                  </div>
                  <Switch
                    checked={notifications.weeklyReports}
                    onCheckedChange={(checked: boolean) => 
                      setNotifications(prev => ({ ...prev, weeklyReports: checked }))
                    }
                  />
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm">Marketing Emails</p>
                    <p className="text-xs text-gray-600">Updates about new features and tips</p>
                  </div>
                  <Switch
                    checked={notifications.marketingEmails}
                    onCheckedChange={(checked: boolean) => 
                      setNotifications(prev => ({ ...prev, marketingEmails: checked }))
                    }
                  />
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
              <Button variant="outline" className="w-full border-green-200 hover:bg-green-50">
                Change Password
              </Button>
              <Button variant="outline" className="w-full border-green-200 hover:bg-green-50">
                Enable Two-Factor Authentication
              </Button>
              <Button variant="outline" className="w-full border-red-200 text-red-600 hover:bg-red-50">
                Delete Account
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}