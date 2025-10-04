import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/navbar';
import { Footer } from './components/footer';
import { Landing } from './components/landing';
import { Login } from './components/login';
import { ForgotPassword } from './components/pages/forgot-password';
import { ResetPassword } from './components/pages/reset-password';
import { ImageUpload } from './components/pages/image-upload';
import { History } from './components/pages/history';
import { Profile } from './components/pages/profile';
import OpenRoute from './components/OpenRoute';
import PrivateRoute from './components/PrivateRoute';
import AppInitializer from './AppInitializer';
import { useSelector } from 'react-redux';
import { RootState } from './redux/store';
import { Loading } from './components/ui/loading';
import { ConfirmEmailChange } from './components/confirm-email-change';
import { ConfirmOtpForSignup } from './components/confirm-otp-for-signup';
import { CropsCoverage } from './components/crops-coverage';

export default function App() {
  const isLoading = useSelector((state: RootState) => state.auth.loading);


  return (
    <>
      <AppInitializer />
      <Router>
        <div className="min-h-screen flex flex-col bg-gradient-to-b from-green-50 to-green-100">
          <Navbar />
          <main className="flex-1">
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={
                <OpenRoute>
                  <Login />
                </OpenRoute>
              } />
              <Route path="/forgot-password" element={
                <OpenRoute>
                  <ForgotPassword />
                </OpenRoute>
              } />
              <Route path="/reset-password" element={
                <PrivateRoute>
                  <ResetPassword />
                </PrivateRoute>
              } />
              <Route path="/confirm-email-change" element={
                <PrivateRoute>
                  <ConfirmEmailChange />
                </PrivateRoute>
              } />
              <Route
                path="/confirm-signup-otp"
                element={
                  <OpenRoute>
                    <ConfirmOtpForSignup />
                  </OpenRoute>
                }
              />
              <Route path="/upload" element={
                <PrivateRoute>
                  <ImageUpload />
                </PrivateRoute>
              } />
              <Route path="/history" element={
                <PrivateRoute>
                  <History />
                </PrivateRoute>
              } />
              <Route path="/update-password/:token" element={<ResetPassword />} />
              <Route path="/profile" element={
                <PrivateRoute>
                  <Profile />
                </PrivateRoute>
              } />

              <Route path="/crops" element={<CropsCoverage />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </Router>

    </>

  );
}