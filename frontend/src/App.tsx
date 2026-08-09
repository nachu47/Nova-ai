import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { AuthProvider } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { AppLayout } from '@/layouts/AppLayout';

import { AdminPage } from '@/pages/AdminPage';
import { AdminOrganizationsPage } from '@/pages/AdminOrganizationsPage';
import { AdminUsersPage } from '@/pages/AdminUsersPage';
import { AdminAgentsPage } from '@/pages/AdminAgentsPage';
import { AdminCallsPage } from '@/pages/AdminCallsPage';
import { AdminActivityPage } from '@/pages/AdminActivityPage';
import { AdminKnowledgePage } from '@/pages/AdminKnowledgePage';
import { AdminBillingPage } from '@/pages/AdminBillingPage';
import { AdminUsagePage } from '@/pages/AdminUsagePage';
import { AdminAuditLogsPage } from '@/pages/AdminAuditLogsPage';
import { AdminPlatformSettingsPage } from '@/pages/AdminPlatformSettingsPage';
import { AdminInfrastructurePage } from '@/pages/AdminInfrastructurePage';
import { AdminSecurityPage } from '@/pages/AdminSecurityPage';
import { AdminSystemSettingsPage } from '@/pages/AdminSystemSettingsPage';

import { AgentsPage } from '@/pages/AgentsPage';
import { AnalyticsPage } from '@/pages/AnalyticsPage';
import { CallsPage } from '@/pages/CallsPage';
import { CRMPage } from '@/pages/CRMPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { IntegrationsPage } from '@/pages/IntegrationsPage';
import { KnowledgePage } from '@/pages/KnowledgePage';
import { LoginPage } from '@/pages/LoginPage';
import { ForgotPasswordPage } from '@/pages/ForgotPasswordPage';
import { ResetPasswordPage } from '@/pages/ResetPasswordPage';
import { VerifyEmailPage } from '@/pages/VerifyEmailPage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { RegisterPage } from '@/pages/RegisterPage';
import { SchedulingPage } from '@/pages/SchedulingPage';
import { SettingsPage } from '@/pages/SettingsPage';

export default function App() {
    return (
        <ThemeProvider>
            <AuthProvider>
                <BrowserRouter>
                    <Routes>
                        <Route path="/login" element={<LoginPage />} />
                        <Route path="/register" element={<RegisterPage />} />
                        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
                        <Route path="/reset-password" element={<ResetPasswordPage />} />
                        <Route path="/verify-email" element={<VerifyEmailPage />} />

                        <Route element={<ProtectedRoute />}>
                            <Route element={<AppLayout />}>
                                <Route index element={<DashboardPage />} />
                                <Route path="calls" element={<CallsPage />} />
                                <Route path="agents" element={<AgentsPage />} />
                                <Route path="crm" element={<CRMPage />} />
                                <Route path="scheduling" element={<SchedulingPage />} />
                                <Route path="knowledge" element={<KnowledgePage />} />
                                <Route path="analytics" element={<AnalyticsPage />} />
                                <Route path="integrations" element={<IntegrationsPage />} />
                                <Route path="settings" element={<SettingsPage />} />

                                {/* Super Admin 14 Modules */}
                                <Route path="admin" element={<AdminPage />} />
                                <Route path="admin/organizations" element={<AdminOrganizationsPage />} />
                                <Route path="admin/users" element={<AdminUsersPage />} />
                                <Route path="admin/agents" element={<AdminAgentsPage />} />
                                <Route path="admin/calls" element={<AdminCallsPage />} />
                                <Route path="admin/activity" element={<AdminActivityPage />} />
                                <Route path="admin/knowledge" element={<AdminKnowledgePage />} />
                                <Route path="admin/billing" element={<AdminBillingPage />} />
                                <Route path="admin/usage" element={<AdminUsagePage />} />
                                <Route path="admin/audit" element={<AdminAuditLogsPage />} />
                                <Route path="admin/audit-logs" element={<AdminAuditLogsPage />} />
                                <Route path="admin/platform" element={<AdminPlatformSettingsPage />} />
                                <Route path="admin/platform-settings" element={<AdminPlatformSettingsPage />} />
                                <Route path="admin/infrastructure" element={<AdminInfrastructurePage />} />
                                <Route path="admin/security" element={<AdminSecurityPage />} />
                                <Route path="admin/settings" element={<AdminSystemSettingsPage />} />

                                <Route path="404" element={<NotFoundPage />} />
                                <Route path="*" element={<Navigate to="/404" replace />} />
                            </Route>
                        </Route>
                    </Routes>
                </BrowserRouter>
            </AuthProvider>
        </ThemeProvider>
    );
}
