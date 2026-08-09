import { ShieldAlert } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useAuth } from '@/contexts/AuthContext';
import { useApi } from '@/hooks/useApi';

type AuditLogItem = {
    id: string;
    action: string;
    entity_type: string;
    entity_id?: string;
    actor_email: string;
    organization_name: string;
    ip_address?: string;
    created_at: string;
};

export function AdminAuditLogsPage() {
    const { user } = useAuth();
    const { data: logs } = useApi<AuditLogItem[]>('/admin/global-audit-logs');

    if (user?.role !== 'superadmin') return <p className="text-destructive">Administrator access is required.</p>;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="page-title">Global Audit & Security Center</h1>
                <p className="page-subtitle">Track all admin events, security changes, and platform actions across tenants.</p>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <ShieldAlert className="h-5 w-5 text-primary" />
                        Audit Log Records
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Timestamp</TableHead>
                                <TableHead>Actor</TableHead>
                                <TableHead>Action</TableHead>
                                <TableHead>Target Entity</TableHead>
                                <TableHead>Organization</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {logs?.map(log => (
                                <TableRow key={log.id}>
                                    <TableCell className="text-xs text-muted-foreground">{new Date(log.created_at).toLocaleString()}</TableCell>
                                    <TableCell className="font-medium">{log.actor_email}</TableCell>
                                    <TableCell><code className="rounded bg-muted px-2 py-0.5 text-xs">{log.action}</code></TableCell>
                                    <TableCell className="text-xs text-muted-foreground">{log.entity_type} ({log.entity_id || 'N/A'})</TableCell>
                                    <TableCell>{log.organization_name}</TableCell>
                                </TableRow>
                            ))}
                            {logs?.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={5} className="py-10 text-center text-muted-foreground">No audit logs found.</TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}
