import { Server } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';
import { useApi } from '@/hooks/useApi';

type DashboardData = { system_health: Record<string, string> };

export function AdminInfrastructurePage() {
    const { user } = useAuth();
    
    // We can just query the dashboard for the health check.
    const { data } = useApi<DashboardData>('/analytics/dashboard');

    if (user?.role !== 'superadmin') return <p className="text-destructive">Administrator access is required.</p>;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="page-title">Platform Infrastructure</h1>
                <p className="page-subtitle">Global system health and integration status.</p>
            </div>
            
            <div className="grid gap-6 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Server className="h-5 w-5 text-primary" />
                            System Health
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {data?.system_health ? (
                            Object.entries(data.system_health).map(([service, status]) => (
                                <div key={service} className="flex items-center justify-between rounded-lg border p-3">
                                    <span className="capitalize">{service}</span>
                                    <Badge className={status === 'healthy' ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-500' : 'text-destructive'}>
                                        {status}
                                    </Badge>
                                </div>
                            ))
                        ) : (
                            <p className="text-sm text-muted-foreground">Loading system health...</p>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
