import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from '@/components/layout';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
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

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected */}
        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
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

        {/* Default redirect */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
