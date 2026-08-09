import { useState } from 'react';
import { Building2, Plus, Power, Edit3, UserCheck, Trash2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useAuth } from '@/contexts/AuthContext';
import { useApi } from '@/hooks/useApi';
import { api } from '@/services/api';

type OrganizationDetail = {
    id: string;
    name: string;
    plan: string;
    owner_name: string;
    owner_email: string;
    owner_role: string;
    users: number;
    voice_agents: number;
    calls: number;
    usage: number;
};

export function AdminOrganizationsPage() {
    const { user: currentUser } = useAuth();
    const { data: orgs, loading, reload } = useApi<OrganizationDetail[]>('/admin/organizations');
    const [actionMsg, setActionMsg] = useState('');
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newOrgName, setNewOrgName] = useState('');
    const [newOrgPlan, setNewOrgPlan] = useState('starter');
    const [editingOrg, setEditingOrg] = useState<OrganizationDetail | null>(null);
    const [selectedPlan, setSelectedPlan] = useState('');

    if (currentUser?.role !== 'superadmin') return <p className="text-destructive">Administrator access is required.</p>;

    async function toggleSuspend(org: OrganizationDetail) {
        const isSuspended = org.plan === 'suspended';
        const action = isSuspended ? 'activate' : 'suspend';
        try {
            await api.post(`/admin/organizations/${org.id}/${action}`);
            setActionMsg(`Organization '${org.name}' has been ${isSuspended ? 'activated' : 'suspended'}.`);
            await reload();
        } catch {
            setActionMsg(`Failed to ${action} organization.`);
        }
    }

    async function handleDeleteOrg(org: OrganizationDetail) {
        if (!confirm(`Are you sure you want to delete organization '${org.name}'? This will remove access for all users in this company.`)) return;
        try {
            await api.delete(`/admin/organizations/${org.id}`);
            setActionMsg(`Organization '${org.name}' deleted successfully.`);
            await reload();
        } catch {
            setActionMsg('Failed to delete organization.');
        }
    }

    async function handleUpdatePlan(e: React.FormEvent) {
        e.preventDefault();
        if (!editingOrg) return;
        try {
            await api.patch(`/admin/organizations/${editingOrg.id}/plan`, { plan: selectedPlan });
            setActionMsg(`Updated plan for '${editingOrg.name}' to ${selectedPlan}.`);
            setEditingOrg(null);
            await reload();
        } catch {
            setActionMsg('Failed to update organization plan.');
        }
    }

    async function handleCreateOrg(e: React.FormEvent) {
        e.preventDefault();
        if (!newOrgName.trim()) return;
        try {
            await api.post('/admin/organizations', { name: newOrgName, plan: newOrgPlan });
            setActionMsg(`Created new organization '${newOrgName}'!`);
            setShowCreateModal(false);
            setNewOrgName('');
            await reload();
        } catch {
            setActionMsg('Failed to create new organization.');
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="page-title">Organizations</h1>
                    <p className="page-subtitle">View and manage all tenant organizations, primary owner users, plans, and platform access.</p>
                </div>
                <Button onClick={() => setShowCreateModal(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Organization
                </Button>
            </div>

            {actionMsg && <p className="text-sm font-medium text-primary">{actionMsg}</p>}

            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Building2 className="h-5 w-5 text-primary" />
                        All Platform Organizations
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Organization</TableHead>
                                <TableHead>Primary Owner / Contact</TableHead>
                                <TableHead>User Type / Role</TableHead>
                                <TableHead>Plan Status</TableHead>
                                <TableHead className="text-right">Users</TableHead>
                                <TableHead className="text-right">Agents</TableHead>
                                <TableHead className="text-right">Calls</TableHead>
                                <TableHead className="text-right">Usage Cost</TableHead>
                                <TableHead>Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {loading && (
                                <TableRow>
                                    <TableCell colSpan={9} className="py-10 text-center text-muted-foreground">Loading organizations...</TableCell>
                                </TableRow>
                            )}

                            {!loading && orgs?.map(org => (
                                <TableRow key={org.id}>
                                    <TableCell className="font-semibold">{org.name}</TableCell>
                                    <TableCell>
                                        <div className="flex items-center gap-2">
                                            <UserCheck className="h-4 w-4 text-primary" />
                                            <div>
                                                <div className="font-medium text-sm">{org.owner_name || 'N/A'}</div>
                                                <div className="text-xs text-muted-foreground">{org.owner_email || 'N/A'}</div>
                                            </div>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <Badge className="capitalize text-xs font-semibold">
                                            {org.owner_role || 'Owner'}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <Badge className={org.plan === 'suspended' ? 'bg-destructive/10 text-destructive border-destructive/30' : 'bg-primary/10 text-primary border-primary/30'}>
                                            {org.plan}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-right font-medium">{org.users}</TableCell>
                                    <TableCell className="text-right font-medium">{org.voice_agents}</TableCell>
                                    <TableCell className="text-right font-medium">{org.calls}</TableCell>
                                    <TableCell className="text-right font-semibold text-emerald-500">${org.usage.toFixed(2)}</TableCell>
                                    <TableCell className="flex items-center gap-2">
                                        <Button size="sm" variant="outline" onClick={() => { setEditingOrg(org); setSelectedPlan(org.plan); }}>
                                            <Edit3 className="h-3.5 w-3.5 mr-1" />
                                            Plan
                                        </Button>
                                        <Button size="sm" variant={org.plan === 'suspended' ? 'default' : 'outline'} onClick={() => void toggleSuspend(org)}>
                                            <Power className="h-3.5 w-3.5 mr-1" />
                                            {org.plan === 'suspended' ? 'Activate' : 'Suspend'}
                                        </Button>
                                        <Button size="sm" variant="destructive" onClick={() => void handleDeleteOrg(org)}>
                                            <Trash2 className="h-3.5 w-3.5 mr-1" />
                                            Delete
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}

                            {!loading && orgs?.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={9} className="py-10 text-center text-muted-foreground">No organizations found on the platform.</TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {/* Create Organization Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
                    <Card className="w-full max-w-md bg-card">
                        <CardHeader>
                            <CardTitle>Create New Organization</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={e => void handleCreateOrg(e)} className="space-y-4">
                                <div>
                                    <label className="text-xs font-medium">Organization / Company Name</label>
                                    <input 
                                        type="text" 
                                        required 
                                        value={newOrgName} 
                                        onChange={e => setNewOrgName(e.target.value)} 
                                        className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm" 
                                        placeholder="e.g. Acme Corporation"
                                    />
                                </div>
                                <div>
                                    <label className="text-xs font-medium">Subscription Plan</label>
                                    <select 
                                        value={newOrgPlan} 
                                        onChange={e => setNewOrgPlan(e.target.value)} 
                                        className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                                    >
                                        <option value="starter">Starter</option>
                                        <option value="pro">Pro</option>
                                        <option value="enterprise">Enterprise</option>
                                    </select>
                                </div>
                                <div className="flex justify-end gap-2 pt-2">
                                    <Button type="button" variant="ghost" onClick={() => setShowCreateModal(false)}>Cancel</Button>
                                    <Button type="submit">Create Organization</Button>
                                </div>
                            </form>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Edit Plan Modal */}
            {editingOrg && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
                    <Card className="w-full max-w-md bg-card">
                        <CardHeader>
                            <CardTitle>Update Plan for {editingOrg.name}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={e => void handleUpdatePlan(e)} className="space-y-4">
                                <div>
                                    <label className="text-xs font-medium">Select Subscription Tier</label>
                                    <select 
                                        value={selectedPlan} 
                                        onChange={e => setSelectedPlan(e.target.value)} 
                                        className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                                    >
                                        <option value="starter">Starter</option>
                                        <option value="pro">Pro</option>
                                        <option value="enterprise">Enterprise</option>
                                        <option value="suspended">Suspended</option>
                                    </select>
                                </div>
                                <div className="flex justify-end gap-2 pt-2">
                                    <Button type="button" variant="ghost" onClick={() => setEditingOrg(null)}>Cancel</Button>
                                    <Button type="submit">Save Plan</Button>
                                </div>
                            </form>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
}
