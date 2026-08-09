import { PhoneCall } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useAuth } from '@/contexts/AuthContext';
import { useApi } from '@/hooks/useApi';
import { duration } from '@/lib/utils';
import type { Call } from '@/types';

type GlobalCallResponse = {
    total: number;
    items: (Call & { organization_name: string })[];
};

export function AdminCallsPage() {
    const { user } = useAuth();
    const { data } = useApi<GlobalCallResponse>('/admin/global-calls');

    if (user?.role !== 'superadmin') return <p className="text-destructive">Administrator access is required.</p>;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="page-title">Global Calls</h1>
                <p className="page-subtitle">View call activity across all organizations.</p>
            </div>
            
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <PhoneCall className="h-5 w-5 text-primary" />
                        Recent Platform Calls (Total: {data?.total ?? 0})
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Organization</TableHead>
                                <TableHead>Number</TableHead>
                                <TableHead>Direction</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Duration</TableHead>
                                <TableHead>Date</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {data?.items.map(call => (
                                <TableRow key={call.id}>
                                    <TableCell className="font-medium">{call.organization_name}</TableCell>
                                    <TableCell>{call.to_number}</TableCell>
                                    <TableCell className="capitalize">{call.direction}</TableCell>
                                    <TableCell><Badge>{call.status}</Badge></TableCell>
                                    <TableCell>{duration(call.duration_seconds)}</TableCell>
                                    <TableCell className="text-xs text-muted-foreground">{new Date(call.created_at).toLocaleString()}</TableCell>
                                </TableRow>
                            ))}
                            {(!data || data.items.length === 0) && (
                                <TableRow>
                                    <TableCell colSpan={6} className="py-10 text-center text-muted-foreground">No calls found.</TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}
