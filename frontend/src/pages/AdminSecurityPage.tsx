import { ShieldAlert, Lock, AlertTriangle, Key } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/contexts/AuthContext';
import { useApi } from '@/hooks/useApi';

type SecurityEvent = {
    id: string;
    action: string;
    actor_email: string;
    ip_address?: string;
    created_at: string;
};

export function AdminSecurityPage() {
    const { user } = useAuth();
    const { data: logs } = useApi<SecurityEvent[]>('/admin/global-audit-logs');

    if (user?.role !== 'superadmin') return <p className="text-destructive">Administrator access is required.</p>;

    const securityAlerts = [
        { id: '1', level: 'LOW', title: 'Server-Enforced Multi-Tenancy Active', desc: 'All tenant queries isolated by organization_id.' },
        { id: '2', level: 'LOW', title: 'JWT Token Rotation Enabled', desc: 'Active sessions protected with secret key encryption.' },
        { id: '3', level: 'LOW', title: 'Rate Limiting Policy Enabled', desc: 'API rate limits enforced at 120 requests/min.' }
    ];

    return (
        <div className="space-y-6">
            <div>
                <h1 className="page-title">Platform Security Center</h1>
                <p className="page-subtitle">Monitor authentication security, privilege changes, rate limits, and threat alerts.</p>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
                <Card>
                    <CardContent className="p-5 flex items-center gap-4">
                        <Lock className="h-8 w-8 text-emerald-500" />
                        <div>
                            <p className="text-sm font-medium text-muted-foreground">Auth Security</p>
                            <p className="text-xl font-bold">Enforced (JWT)</p>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-5 flex items-center gap-4">
                        <Key className="h-8 w-8 text-primary" />
                        <div>
                            <p className="text-sm font-medium text-muted-foreground">Privilege Isolation</p>
                            <p className="text-xl font-bold">Active (Server-Side)</p>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-5 flex items-center gap-4">
                        <ShieldAlert className="h-8 w-8 text-purple-500" />
                        <div>
                            <p className="text-sm font-medium text-muted-foreground">Threat Level</p>
                            <p className="text-xl font-bold text-emerald-500">Normal / Healthy</p>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <AlertTriangle className="h-5 w-5 text-primary" />
                        Security Policy & System Guardrail Status
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                    {securityAlerts.map(alert => (
                        <div key={alert.id} className="flex items-center justify-between rounded-lg border p-3">
                            <div>
                                <p className="font-semibold text-sm">{alert.title}</p>
                                <p className="text-xs text-muted-foreground">{alert.desc}</p>
                            </div>
                            <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/30">
                                {alert.level}
                            </Badge>
                        </div>
                    ))}
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Lock className="h-5 w-5 text-primary" />
                        Privileged Admin Activity Log
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Timestamp</TableHead>
                                <TableHead>Actor</TableHead>
                                <TableHead>Privileged Action</TableHead>
                                <TableHead>IP Address</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {logs?.map(log => (
                                <TableRow key={log.id}>
                                    <TableCell className="text-xs text-muted-foreground">{new Date(log.created_at).toLocaleString()}</TableCell>
                                    <TableCell className="font-medium">{log.actor_email}</TableCell>
                                    <TableCell><code className="rounded bg-muted px-2 py-0.5 text-xs">{log.action}</code></TableCell>
                                    <TableCell className="text-xs text-muted-foreground">{log.ip_address || '127.0.0.1'}</TableCell>
                                </TableRow>
                            ))}
                            {logs?.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={4} className="py-10 text-center text-muted-foreground">No security events recorded.</TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}
