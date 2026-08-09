import { Contact, Building2, Briefcase, CheckSquare } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';
import { useApi } from '@/hooks/useApi';

type ActivityOverview = {
    organizations: number;
    users: number;
    calls: number;
};

export function AdminActivityPage() {
    const { user } = useAuth();
    const { data } = useApi<ActivityOverview>('/admin/platform');

    if (user?.role !== 'superadmin') return <p className="text-destructive">Administrator access is required.</p>;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="page-title">CRM & Platform Activity</h1>
                <p className="page-subtitle">Global overview of CRM pipelines, deals, contacts, and organization activity.</p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardContent className="p-5 flex items-center gap-3">
                        <Building2 className="h-6 w-6 text-primary" />
                        <div>
                            <p className="text-2xl font-bold">{data?.organizations ?? 0}</p>
                            <p className="text-xs text-muted-foreground">Active Companies</p>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-5 flex items-center gap-3">
                        <Contact className="h-6 w-6 text-emerald-500" />
                        <div>
                            <p className="text-2xl font-bold">{data?.users ?? 0}</p>
                            <p className="text-xs text-muted-foreground">Active CRM Users</p>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-5 flex items-center gap-3">
                        <Briefcase className="h-6 w-6 text-purple-500" />
                        <div>
                            <p className="text-2xl font-bold">Active</p>
                            <p className="text-xs text-muted-foreground">Deals Pipelines</p>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-5 flex items-center gap-3">
                        <CheckSquare className="h-6 w-6 text-blue-500" />
                        <div>
                            <p className="text-2xl font-bold">{data?.calls ?? 0}</p>
                            <p className="text-xs text-muted-foreground">Completed Tasks / Calls</p>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Cross-Tenant Activity Signals</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-muted-foreground py-6 text-center">
                        All organization CRM pipelines, deals, contacts, and tasks are strictly isolated per tenant. High-level aggregates are tracked above.
                    </p>
                </CardContent>
            </Card>
        </div>
    );
}
