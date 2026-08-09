import { useState } from 'react';
import { Users, UserPlus, Power, Trash2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useAuth } from '@/contexts/AuthContext';
import { useApi } from '@/hooks/useApi';
import { api } from '@/services/api';
import type { User } from '@/types';

type GlobalUser = User & { organization_name: string };
type OrganizationStat = { id: string; name: string };

export function AdminUsersPage() {
    const { user: currentUser } = useAuth();
    const { data: users, loading, reload } = useApi<GlobalUser[]>('/admin/global-users');
    const { data: orgs, reload: reloadOrgs } = useApi<OrganizationStat[]>('/admin/organizations');

    const [showModal, setShowModal] = useState(false);
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState('member');
    const [orgId, setOrgId] = useState('');
    const [newOrgName, setNewOrgName] = useState('');
    const [msg, setMsg] = useState('');

    if (currentUser?.role !== 'superadmin') return <p className="text-destructive">Administrator access is required.</p>;

    async function handleCreateUser(e: React.FormEvent) {
        e.preventDefault();
        try {
            let targetOrgId = orgId;
            if (orgId === 'CREATE_NEW' || (!orgId && newOrgName.trim())) {
                const createdOrg = await api.post<{ id: string }>('/admin/organizations', { 
                    name: newOrgName.trim() || `${fullName}'s Company` 
                });
                targetOrgId = createdOrg.data.id;
                await reloadOrgs();
            }

            if (!targetOrgId && orgs?.[0]?.id) {
                targetOrgId = orgs[0].id;
            }

            await api.post('/admin/global-users', {
                full_name: fullName,
                email,
                password,
                role,
                organization_id: targetOrgId
            });

            setMsg(`User '${fullName}' created successfully!`);
            setShowModal(false);
            setFullName('');
            setEmail('');
            setPassword('');
            setOrgId('');
            setNewOrgName('');
            await reload();
        } catch {
            setMsg('Failed to create user. Please check if the email already exists.');
        }
    }

    async function toggleActive(userItem: GlobalUser) {
        try {
            await api.patch(`/admin/global-users/${userItem.id}`, { is_active: !userItem.is_active });
            setMsg(`Updated status for '${userItem.full_name}'.`);
            await reload();
        } catch {
            setMsg('Failed to update user status.');
        }
    }

    async function handleDeleteUser(userItem: GlobalUser) {
        if (!confirm(`Are you sure you want to permanently delete user '${userItem.full_name}' (${userItem.email})?`)) return;
        try {
            await api.delete(`/admin/global-users/${userItem.id}`);
            setMsg(`User '${userItem.full_name}' has been deleted.`);
            await reload();
        } catch {
            setMsg('Failed to delete user.');
        }
    }

    const getRoleBadge = (roleName: string) => {
        switch (roleName) {
            case 'superadmin':
                return <Badge className="bg-purple-500/15 text-purple-600 border-purple-300 capitalize font-semibold">Super Admin</Badge>;
            case 'owner':
                return <Badge className="bg-blue-500/15 text-blue-600 border-blue-300 capitalize font-semibold">Owner</Badge>;
            case 'admin':
                return <Badge className="bg-emerald-500/15 text-emerald-600 border-emerald-300 capitalize font-semibold">Admin</Badge>;
            default:
                return <Badge className="capitalize">{roleName}</Badge>;
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="page-title">Global Users</h1>
                    <p className="page-subtitle">View, create, manage, and delete user accounts and roles across the platform.</p>
                </div>
                <Button onClick={() => setShowModal(true)}>
                    <UserPlus className="h-4 w-4 mr-2" />
                    Add New User
                </Button>
            </div>

            {msg && <p className="text-sm font-medium text-primary">{msg}</p>}

            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Users className="h-5 w-5 text-primary" />
                        All Platform Users
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>User Account</TableHead>
                                <TableHead>Organization</TableHead>
                                <TableHead>User Type / Role</TableHead>
                                <TableHead>Account Status</TableHead>
                                <TableHead>Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {loading && (
                                <TableRow>
                                    <TableCell colSpan={5} className="py-10 text-center text-muted-foreground">Loading platform users...</TableCell>
                                </TableRow>
                            )}

                            {!loading && users?.map(target => (
                                <TableRow key={target.id}>
                                    <TableCell>
                                        <div className="font-semibold text-sm">{target.full_name}</div>
                                        <div className="text-xs text-muted-foreground">{target.email}</div>
                                    </TableCell>
                                    <TableCell className="font-medium">{target.organization_name}</TableCell>
                                    <TableCell>{getRoleBadge(target.role)}</TableCell>
                                    <TableCell>
                                        <Badge className={target.is_active ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30' : 'bg-destructive/10 text-destructive border-destructive/30'}>
                                            {target.is_active ? 'Active' : 'Inactive'}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="flex items-center gap-2">
                                        <Button 
                                            size="sm" 
                                            variant="outline" 
                                            disabled={target.id === currentUser?.id}
                                            onClick={() => void toggleActive(target)}
                                        >
                                            <Power className="h-3.5 w-3.5 mr-1" />
                                            {target.is_active ? 'Deactivate' : 'Activate'}
                                        </Button>
                                        <Button 
                                            size="sm" 
                                            variant="destructive" 
                                            disabled={target.id === currentUser?.id}
                                            onClick={() => void handleDeleteUser(target)}
                                        >
                                            <Trash2 className="h-3.5 w-3.5 mr-1" />
                                            Delete
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}

                            {!loading && users?.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={5} className="py-10 text-center text-muted-foreground">No users found on the platform.</TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {/* Add User Modal */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
                    <Card className="w-full max-w-md bg-card">
                        <CardHeader>
                            <CardTitle>Add New User</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={e => void handleCreateUser(e)} className="space-y-4">
                                <div>
                                    <label className="text-xs font-medium">Full Name</label>
                                    <input 
                                        type="text" 
                                        required 
                                        value={fullName} 
                                        onChange={e => setFullName(e.target.value)} 
                                        className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm" 
                                        placeholder="John Doe"
                                    />
                                </div>
                                <div>
                                    <label className="text-xs font-medium">Email Address</label>
                                    <input 
                                        type="email" 
                                        required 
                                        value={email} 
                                        onChange={e => setEmail(e.target.value)} 
                                        className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm" 
                                        placeholder="user@company.com"
                                    />
                                </div>
                                <div>
                                    <label className="text-xs font-medium">Password</label>
                                    <input 
                                        type="password" 
                                        required 
                                        value={password} 
                                        onChange={e => setPassword(e.target.value)} 
                                        className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm" 
                                        placeholder="••••••••"
                                    />
                                </div>
                                <div>
                                    <label className="text-xs font-medium">Organization / Company</label>
                                    <select 
                                        value={orgId} 
                                        onChange={e => setOrgId(e.target.value)} 
                                        className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                                    >
                                        <option value="">Select Existing Organization...</option>
                                        {orgs?.map(org => (
                                            <option key={org.id} value={org.id}>{org.name}</option>
                                        ))}
                                        <option value="CREATE_NEW">➕ Create New Isolated Company / Organization</option>
                                    </select>
                                </div>

                                {orgId === 'CREATE_NEW' && (
                                    <div>
                                        <label className="text-xs font-medium text-primary">New Company Name</label>
                                        <input 
                                            type="text" 
                                            required 
                                            value={newOrgName} 
                                            onChange={e => setNewOrgName(e.target.value)} 
                                            className="mt-1 w-full rounded-md border border-primary bg-background px-3 py-2 text-sm" 
                                            placeholder="e.g. Nachu Tech Corp"
                                        />
                                    </div>
                                )}

                                <div>
                                    <label className="text-xs font-medium">User Type / Role</label>
                                    <select 
                                        value={role} 
                                        onChange={e => setRole(e.target.value)} 
                                        className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                                    >
                                        <option value="owner">Owner (Full Company Control)</option>
                                        <option value="admin">Admin</option>
                                        <option value="member">Member</option>
                                        <option value="viewer">Viewer</option>
                                        <option value="superadmin">Super Admin (Platform Level)</option>
                                    </select>
                                </div>
                                <div className="flex justify-end gap-2 pt-2">
                                    <Button type="button" variant="ghost" onClick={() => setShowModal(false)}>Cancel</Button>
                                    <Button type="submit">Create User</Button>
                                </div>
                            </form>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
}
