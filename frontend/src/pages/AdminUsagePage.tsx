import { BarChart3, Clock, Zap, DollarSign } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';
import { useApi } from '@/hooks/useApi';

type RevenueData = {
    total_revenue: number;
    total_usage_events: number;
    top_organizations: { name: string; total: number }[];
};

export function AdminUsagePage() {
    const { user } = useAuth();
    const { data } = useApi<RevenueData>('/admin/revenue-analytics');

    if (user?.role !== 'superadmin') return <p className="text-destructive">Administrator access is required.</p>;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="page-title">AI Usage & Cost Center</h1>
                <p className="page-subtitle">Track OpenAI Realtime Voice minutes, ElevenLabs TTS, Twilio telecom, and token consumption costs.</p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardContent className="p-5 flex items-center gap-3">
                        <Clock className="h-6 w-6 text-primary" />
                        <div>
                            <p className="text-xl font-bold">{data?.total_usage_events ?? 0}</p>
                            <p className="text-xs text-muted-foreground">Usage Events Logged</p>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-5 flex items-center gap-3">
                        <Zap className="h-6 w-6 text-emerald-500" />
                        <div>
                            <p className="text-xl font-bold">gpt-realtime</p>
                            <p className="text-xs text-muted-foreground">Primary Voice Model</p>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-5 flex items-center gap-3">
                        <DollarSign className="h-6 w-6 text-purple-500" />
                        <div>
                            <p className="text-xl font-bold">${(data?.total_revenue ?? 0).toFixed(2)}</p>
                            <p className="text-xs text-muted-foreground">Total Consumption Revenue</p>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-5 flex items-center gap-3">
                        <BarChart3 className="h-6 w-6 text-blue-500" />
                        <div>
                            <p className="text-xl font-bold">~65%</p>
                            <p className="text-xs text-muted-foreground">Estimated Gross Margin</p>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Usage & AI Service Consumption Summary</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                    <div className="flex justify-between items-center p-3 border rounded-lg">
                        <div>
                            <p className="font-semibold text-sm">OpenAI Realtime Voice API</p>
                            <p className="text-xs text-muted-foreground">Speech-to-Speech WebSockets stream</p>
                        </div>
                        <span className="text-xs font-semibold text-emerald-500 bg-emerald-500/10 px-2.5 py-1 rounded">Active</span>
                    </div>

                    <div className="flex justify-between items-center p-3 border rounded-lg">
                        <div>
                            <p className="font-semibold text-sm">Twilio Programmable Voice & Streams</p>
                            <p className="text-xs text-muted-foreground">SIP / Inbound & Outbound Telephony</p>
                        </div>
                        <span className="text-xs font-semibold text-emerald-500 bg-emerald-500/10 px-2.5 py-1 rounded">Active</span>
                    </div>

                    <div className="flex justify-between items-center p-3 border rounded-lg">
                        <div>
                            <p className="font-semibold text-sm">ElevenLabs Voice Synthesizer</p>
                            <p className="text-xs text-muted-foreground">High fidelity TTS voice generation</p>
                        </div>
                        <span className="text-xs font-semibold text-emerald-500 bg-emerald-500/10 px-2.5 py-1 rounded">Active</span>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
