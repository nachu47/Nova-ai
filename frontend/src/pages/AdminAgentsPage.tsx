import { Bot } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useAuth } from '@/contexts/AuthContext';
import { useApi } from '@/hooks/useApi';

type GlobalAgent = { id: string; name: string; system_prompt: string; organization_name: string; created_at: string };

export function AdminAgentsPage() {
    const { user } = useAuth();
    const { data: agents } = useApi<GlobalAgent[]>('/admin/global-agents');

    if (user?.role !== 'superadmin') return <p className="text-destructive">Administrator access is required.</p>;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="page-title">Global AI Agents</h1>
                <p className="page-subtitle">View all AI voice agents across the entire platform.</p>
            </div>
            
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Bot className="h-5 w-5 text-primary" />
                        All AI Agents
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Agent Name</TableHead>
                                <TableHead>Organization</TableHead>
                                <TableHead>Prompt Snippet</TableHead>
                                <TableHead>Created</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {agents?.map(agent => (
                                <TableRow key={agent.id}>
                                    <TableCell className="font-medium">{agent.name}</TableCell>
                                    <TableCell>{agent.organization_name}</TableCell>
                                    <TableCell className="max-w-xs truncate text-muted-foreground">{agent.system_prompt || 'No prompt configured'}</TableCell>
                                    <TableCell className="text-xs text-muted-foreground">{new Date(agent.created_at).toLocaleString()}</TableCell>
                                </TableRow>
                            ))}
                            {agents?.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={4} className="py-10 text-center text-muted-foreground">No agents found.</TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}
