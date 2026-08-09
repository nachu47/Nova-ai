import { DollarSign, TrendingUp, CreditCard } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useAuth } from '@/contexts/AuthContext';
import { useApi } from '@/hooks/useApi';

type RevenueData = {
    total_revenue: number;
    total_usage_events: number;
    top_organizations: { name: string; total: number }[];
};

export function AdminBillingPage() {
    const { user } = useAuth();
    const { data } = useApi<RevenueData>('/admin/revenue-analytics');

    if (user?.role !== 'superadmin') return <p className="text-destructive">Administrator access is required.</p>;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="page-title">Revenue & Usage Billing Analytics</h1>
                <p className="page-subtitle">Track platform-wide revenue generation and tenant usage consumption.</p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <Card>
                    <CardContent className="p-5">
                        <DollarSign className="h-5 w-5 text-primary" />
                        <p className="mt-3 text-3xl font-bold">${(data?.total_revenue ?? 0).toFixed(2)}</p>
                        <p className="text-sm text-muted-foreground">Total Usage Revenue</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-5">
                        <TrendingUp className="h-5 w-5 text-primary" />
                        <p className="mt-3 text-3xl font-bold">{data?.total_usage_events ?? 0}</p>
                        <p className="text-sm text-muted-foreground">Recorded Usage Events</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-5">
                        <CreditCard className="h-5 w-5 text-primary" />
                        <p className="mt-3 text-3xl font-bold">Standard</p>
                        <p className="text-sm text-muted-foreground">Billing Gateway Status</p>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <DollarSign className="h-5 w-5 text-primary" />
                        Top Revenue Generating Organizations
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Rank</TableHead>
                                <TableHead>Organization Name</TableHead>
                                <TableHead className="text-right">Total Billed Usage</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {data?.top_organizations.map((org, index) => (
                                <TableRow key={org.name}>
                                    <TableCell className="font-semibold">#{index + 1}</TableCell>
                                    <TableCell>{org.name}</TableCell>
                                    <TableCell className="text-right font-medium text-emerald-500">${org.total.toFixed(2)}</TableCell>
                                </TableRow>
                            ))}
                            {(!data || data.top_organizations.length === 0) && (
                                <TableRow>
                                    <TableCell colSpan={3} className="py-10 text-center text-muted-foreground">No revenue events recorded yet.</TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}
