import { useState, type ComponentType } from 'react';
import { NavLink, Outlet, Navigate, useLocation } from 'react-router-dom';
import { 
    Activity, BarChart3, Bot, Brain, CalendarDays, ChevronLeft, Contact, 
    LayoutDashboard, Menu, PhoneCall, Plug, Settings, ShieldCheck, SunMoon, 
    Building2, Users, Server, ShieldAlert, Sliders, DollarSign, Lock, Zap, FileText
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { cn } from '@/lib/utils';

type NavItem = { to: string; label: string; icon: ComponentType<{ className?: string }>; admin?: boolean };

const navigation: NavItem[] = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/calls', label: 'Calls', icon: PhoneCall },
    { to: '/agents', label: 'Voice Agents', icon: Bot },
    { to: '/crm', label: 'CRM', icon: Contact },
    { to: '/scheduling', label: 'Scheduling', icon: CalendarDays },
    { to: '/knowledge', label: 'Knowledge', icon: Brain },
    { to: '/analytics', label: 'Analytics', icon: BarChart3 },
    { to: '/integrations', label: 'Integrations', icon: Plug },
    { to: '/settings', label: 'Settings', icon: Settings },
    { to: '/admin', label: 'Admin', icon: ShieldCheck, admin: true },
];

const superAdminNavigation: NavItem[] = [
    { to: '/admin', label: 'Overview', icon: LayoutDashboard },
    { to: '/admin/organizations', label: 'Organizations', icon: Building2 },
    { to: '/admin/users', label: 'Users', icon: Users },
    { to: '/admin/agents', label: 'AI Agents', icon: Bot },
    { to: '/admin/calls', label: 'Calls', icon: PhoneCall },
    { to: '/admin/activity', label: 'CRM / Activity', icon: Contact },
    { to: '/admin/knowledge', label: 'Knowledge & RAG', icon: FileText },
    { to: '/admin/billing', label: 'Billing & Revenue', icon: DollarSign },
    { to: '/admin/usage', label: 'Usage & Costs', icon: Zap },
    { to: '/admin/audit', label: 'Audit Logs', icon: ShieldAlert },
    { to: '/admin/platform', label: 'Platform Controls', icon: Sliders },
    { to: '/admin/infrastructure', label: 'Infrastructure', icon: Server },
    { to: '/admin/security', label: 'Security Center', icon: Lock },
    { to: '/admin/settings', label: 'System Settings', icon: Settings },
];

export function AppLayout() {
    const [open, setOpen] = useState(false);
    const { user, logout } = useAuth();
    const { toggle } = useTheme();
    const location = useLocation();

    if (user?.role === 'superadmin' && !location.pathname.startsWith('/admin')) {
        return <Navigate to="/admin" replace />;
    }

    const links = user?.role === 'superadmin' 
        ? superAdminNavigation 
        : navigation.filter(item => !item.admin || user?.role === 'owner' || user?.role === 'admin');

    return (
        <div className="min-h-screen bg-background">
            <aside className={cn('fixed inset-y-0 left-0 z-50 w-64 border-r bg-card transition-transform lg:translate-x-0 overflow-y-auto', open ? 'translate-x-0' : '-translate-x-full')}>
                <div className="flex h-16 items-center justify-between border-b px-5 sticky top-0 bg-card z-10">
                    <div className="flex items-center gap-2">
                        <div className="grid h-9 w-9 place-items-center rounded-xl bg-primary text-primary-foreground">
                            <Activity className="h-5 w-5" />
                        </div>
                        <div>
                            <p className="font-semibold">{user?.role === 'superadmin' ? 'Global Platform' : 'Nova AI'}</p>
                            <p className="text-[11px] text-muted-foreground">{user?.role === 'superadmin' ? 'Command Center' : 'Calling'}</p>
                        </div>
                    </div>
                    <Button className="lg:hidden" variant="ghost" size="icon" onClick={() => setOpen(false)}>
                        <ChevronLeft className="h-5 w-5" />
                    </Button>
                </div>
                <nav className="space-y-1 p-3 pb-24">
                    {links.map(({ to, label, icon: Icon }) => (
                        <NavLink 
                            key={to} 
                            to={to} 
                            end={to === '/' || to === '/admin'} 
                            onClick={() => setOpen(false)} 
                            className={({ isActive }) => cn('flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors', isActive ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-muted hover:text-foreground')}
                        >
                            <Icon className="h-4 w-4" />
                            {label}
                        </NavLink>
                    ))}
                </nav>
                <div className="absolute inset-x-3 bottom-3 rounded-xl border bg-background p-3">
                    <p className="truncate text-sm font-medium">{user?.full_name}</p>
                    <p className="truncate text-xs text-muted-foreground">{user?.email}</p>
                    <button onClick={() => void logout()} className="mt-2 text-xs text-destructive hover:underline">Sign out</button>
                </div>
            </aside>
            <div className="lg:pl-64">
                <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b bg-background/85 px-4 backdrop-blur md:px-6">
                    <div className="flex items-center gap-3">
                        <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setOpen(true)}>
                            <Menu className="h-5 w-5" />
                        </Button>
                        <div className="hidden text-sm text-muted-foreground sm:block">
                            {user?.role === 'superadmin' ? 'Global Platform Operations Center' : 'AI Voice Operations Command Centre'}
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <Button variant="ghost" size="icon" onClick={toggle} aria-label="Toggle colour mode">
                            <SunMoon className="h-5 w-5" />
                        </Button>
                        <div className="hidden rounded-full bg-muted px-3 py-1.5 text-xs font-medium sm:block uppercase">
                            {user?.role}
                        </div>
                    </div>
                </header>
                <main className="p-4 md:p-6 lg:p-8">
                    <Outlet />
                </main>
            </div>
            {open && <button className="fixed inset-0 z-40 bg-black/60 lg:hidden" onClick={() => setOpen(false)} aria-label="Close menu" />}
        </div>
    );
}
