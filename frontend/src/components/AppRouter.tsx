import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from '@/components/layout';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { HomePage } from '@/pages/HomePage';
import { LoginPage } from '@/pages/LoginPage';
import { RegisterPage } from '@/pages/RegisterPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { OrdersPage } from '@/pages/OrdersPage';
import { ServicesPage } from '@/pages/ServicesPage';
import { CustomersPage } from '@/pages/CustomersPage';
import { StaffPage } from '@/pages/StaffPage';
import { AIChatPage } from '@/pages/AIChatPage';
import { DispatchPage } from '@/pages/DispatchPage';
import { MarketingPage } from '@/pages/MarketingPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { OnboardingPage } from '@/pages/OnboardingPage';
import { H5HomePage } from '@/pages/h5/H5HomePage';
import { H5OrdersPage } from '@/pages/h5/H5OrdersPage';
import { H5OrderDetailPage } from '@/pages/h5/H5OrderDetailPage';
import { H5ReviewPage } from '@/pages/h5/H5ReviewPage';
import { StaffLoginPage } from '@/pages/staffApp/StaffLoginPage';
import { StaffHomePage } from '@/pages/staffApp/StaffHomePage';
import { StaffOrderDetailPage } from '@/pages/staffApp/StaffOrderDetailPage';
import { StaffProfilePage } from '@/pages/staffApp/StaffProfilePage';

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public — H5 Customer Self-Service (no auth) */}
        <Route path="/h5/:customerId" element={<H5HomePage />} />
        <Route path="/h5/:customerId/orders" element={<H5OrdersPage />} />
        <Route path="/h5/:customerId/orders/:orderId" element={<H5OrderDetailPage />} />
        <Route path="/h5/:customerId/orders/:orderId/review" element={<H5ReviewPage />} />

        {/* Public — Staff PWA (no auth, token-based) */}
        <Route path="/staff-app/login" element={<StaffLoginPage />} />
        <Route path="/staff-app/:staffId" element={<StaffHomePage />} />
        <Route path="/staff-app/:staffId/orders/:orderId" element={<StaffOrderDetailPage />} />
        <Route path="/staff-app/:staffId/profile" element={<StaffProfilePage />} />

        {/* Public */}
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected */}
        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
            <Route path="/onboarding" element={<OnboardingPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/orders" element={<OrdersPage />} />
            <Route path="/services" element={<ServicesPage />} />
            <Route path="/customers" element={<CustomersPage />} />
            <Route path="/staff" element={<StaffPage />} />
            <Route path="/ai-chat" element={<AIChatPage />} />
            <Route path="/dispatch" element={<DispatchPage />} />
            <Route path="/marketing" element={<MarketingPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Route>

        {/* Catch-all → home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
