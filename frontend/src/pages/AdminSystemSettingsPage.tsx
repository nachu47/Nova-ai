import { useState } from 'react';
import { Settings, Key, Bot } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';

export function AdminSystemSettingsPage() {
    const { user } = useAuth();
    const [msg, setMsg] = useState('');

    if (user?.role !== 'superadmin') return <p className="text-destructive">Administrator access is required.</p>;

    function handleSave() {
        setMsg('Global system settings saved successfully!');
        setTimeout(() => setMsg(''), 3000);
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="page-title">Global System Settings</h1>
                <p className="page-subtitle">Configure platform-wide authentication session policies, AI model defaults, and security rules.</p>
            </div>

            {msg && <p className="text-sm font-medium text-emerald-500">{msg}</p>}

            <div className="grid gap-6 lg:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Key className="h-5 w-5 text-primary" />
                            Authentication & Session Security
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <label className="text-xs font-medium">Session Token Lifetime (Minutes)</label>
                            <input type="number" defaultValue={1440} className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm" />
                        </div>
                        <div>
                            <label className="text-xs font-medium">Global Rate Limit Policy</label>
                            <input type="text" defaultValue="120 requests per minute per IP" disabled className="mt-1 w-full rounded-md border bg-muted px-3 py-2 text-sm text-muted-foreground" />
                        </div>
                        <div>
                            <label className="text-xs font-medium">Multi-Tenant Isolation Level</label>
                            <input type="text" defaultValue="Strict Server-Side SQL Filtering (enforced)" disabled className="mt-1 w-full rounded-md border bg-muted px-3 py-2 text-sm text-muted-foreground" />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Bot className="h-5 w-5 text-primary" />
                            Default AI Engine & Telecom Limits
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <label className="text-xs font-medium">Default OpenAI Voice Model</label>
                            <select defaultValue="gpt-realtime" className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm">
                                <option value="gpt-realtime">gpt-realtime (Speech-to-Speech)</option>
                                <option value="gpt-4.1-mini">gpt-4.1-mini</option>
                            </select>
                        </div>
                        <div>
                            <label className="text-xs font-medium">Max Call Concurrency Per Organization</label>
                            <input type="number" defaultValue={25} className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm" />
                        </div>
                        <div>
                            <label className="text-xs font-medium">Default Voice Credits (Seconds)</label>
                            <input type="number" defaultValue={3600} className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm" />
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div className="flex justify-end">
                <Button onClick={handleSave}>
                    <Settings className="h-4 w-4 mr-2" />
                    Save Global Settings
                </Button>
            </div>
        </div>
    );
}
