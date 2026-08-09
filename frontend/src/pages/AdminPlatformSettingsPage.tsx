import { useState } from 'react';
import { Sliders, Megaphone, Trash2, Plus } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';
import { useApi } from '@/hooks/useApi';
import { api } from '@/services/api';

type Announcement = { id: string; title: string; message: string; level: string; created_at: string };

export function AdminPlatformSettingsPage() {
    const { user } = useAuth();
    const { data: flags, reload: reloadFlags } = useApi<Record<string, boolean>>('/admin/feature-flags');
    const { data: announcements, reload: reloadAnnouncements } = useApi<Announcement[]>('/admin/announcements');

    const [newTitle, setNewTitle] = useState('');
    const [newMessage, setNewMessage] = useState('');
    const [newLevel, setNewLevel] = useState('info');
    const [statusMsg, setStatusMsg] = useState('');

    if (user?.role !== 'superadmin') return <p className="text-destructive">Administrator access is required.</p>;

    async function toggleFlag(key: string, current: boolean) {
        try {
            await api.put(`/admin/feature-flags/${key}`, { enabled: !current });
            setStatusMsg(`Toggled feature flag '${key}'.`);
            await reloadFlags();
        } catch {
            setStatusMsg('Failed to toggle feature flag.');
        }
    }

    async function handleCreateAnnouncement(e: React.FormEvent) {
        e.preventDefault();
        if (!newTitle.trim() || !newMessage.trim()) return;
        try {
            await api.post('/admin/announcements', { title: newTitle, message: newMessage, level: newLevel });
            setNewTitle('');
            setNewMessage('');
            setStatusMsg('Broadcast announcement created!');
            await reloadAnnouncements();
        } catch {
            setStatusMsg('Failed to create announcement.');
        }
    }

    async function handleDeleteAnnouncement(id: string) {
        try {
            await api.delete(`/admin/announcements/${id}`);
            setStatusMsg('Announcement removed.');
            await reloadAnnouncements();
        } catch {
            setStatusMsg('Failed to delete announcement.');
        }
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="page-title">Platform Controls & Announcements</h1>
                <p className="page-subtitle">Toggle dynamic platform capabilities and broadcast system-wide banners.</p>
            </div>

            {statusMsg && <p className="text-sm font-medium text-primary">{statusMsg}</p>}

            <div className="grid gap-6 lg:grid-cols-2">
                {/* Dynamic Feature Flags */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Sliders className="h-5 w-5 text-primary" />
                            Dynamic Feature Flags
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {flags ? (
                            Object.entries(flags).map(([key, enabled]) => (
                                <div key={key} className="flex items-center justify-between rounded-lg border p-3">
                                    <div>
                                        <p className="font-medium capitalize">{key.replace('ff_', '').replace(/_/g, ' ')}</p>
                                        <p className="text-xs text-muted-foreground">{key}</p>
                                    </div>
                                    <Button 
                                        size="sm" 
                                        variant={enabled ? 'default' : 'outline'}
                                        onClick={() => void toggleFlag(key, enabled)}
                                    >
                                        {enabled ? 'Enabled' : 'Disabled'}
                                    </Button>
                                </div>
                            ))
                        ) : (
                            <p className="text-sm text-muted-foreground">Loading feature flags...</p>
                        )}
                    </CardContent>
                </Card>

                {/* Broadcast Announcements */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Megaphone className="h-5 w-5 text-primary" />
                            Global Announcements
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <form onSubmit={e => void handleCreateAnnouncement(e)} className="space-y-3 rounded-lg border p-3 bg-muted/30">
                            <p className="text-xs font-semibold uppercase text-muted-foreground">New Broadcast Banner</p>
                            <input 
                                type="text" 
                                placeholder="Title (e.g. Scheduled Maintenance)" 
                                value={newTitle} 
                                onChange={e => setNewTitle(e.target.value)} 
                                className="w-full rounded-md border bg-background px-3 py-1.5 text-sm" 
                                required 
                            />
                            <textarea 
                                placeholder="Message details..." 
                                value={newMessage} 
                                onChange={e => setNewMessage(e.target.value)} 
                                className="w-full rounded-md border bg-background px-3 py-1.5 text-sm h-20" 
                                required 
                            />
                            <div className="flex items-center justify-between">
                                <select 
                                    value={newLevel} 
                                    onChange={e => setNewLevel(e.target.value)} 
                                    className="rounded-md border bg-background px-3 py-1 text-sm"
                                >
                                    <option value="info">Info (Blue)</option>
                                    <option value="warning">Warning (Yellow)</option>
                                    <option value="urgent">Urgent (Red)</option>
                                </select>
                                <Button size="sm" type="submit">
                                    <Plus className="h-4 w-4 mr-1" /> Broadcast
                                </Button>
                            </div>
                        </form>

                        <div className="space-y-2">
                            {announcements?.map(item => (
                                <div key={item.id} className="flex items-start justify-between rounded-lg border p-3">
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <span className="font-semibold">{item.title}</span>
                                            <Badge className="capitalize text-[10px]">{item.level}</Badge>
                                        </div>
                                        <p className="mt-1 text-sm text-muted-foreground">{item.message}</p>
                                        <p className="mt-2 text-[10px] text-muted-foreground">{new Date(item.created_at).toLocaleString()}</p>
                                    </div>
                                    <Button size="icon" variant="ghost" className="h-8 w-8 text-destructive" onClick={() => void handleDeleteAnnouncement(item.id)}>
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </div>
                            ))}
                            {announcements?.length === 0 && (
                                <p className="py-4 text-center text-xs text-muted-foreground">No active announcements.</p>
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
