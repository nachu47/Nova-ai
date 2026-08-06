import { useState, type FormEvent } from 'react';
import { PhoneCall, Play, FileText, X } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useApi } from '@/hooks/useApi';
import { duration, money } from '@/lib/utils';
import { api, errorMessage } from '@/services/api';
import type { Agent, Call, Paginated, CallSummary } from '@/types';

export function CallsPage() {
  const { data, reload, loading } = useApi<Paginated<Call>>('/calls?page_size=100');
  const { data: agents } = useApi<Agent[]>('/agents');
  
  const [agentId, setAgentId] = useState('');
  const [countryCode, setCountryCode] = useState('+1');
  const [number, setNumber] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  // Summary Modal State
  const [selectedCallId, setSelectedCallId] = useState<string | null>(null);
  const [summary, setSummary] = useState<CallSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState('');

  async function create(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMessage('');
    
    // Ensure the number is properly formatted with the country code
    let formattedNumber = number.trim();
    if (!formattedNumber.startsWith('+')) {
      // Remove any leading zeros if they typed it
      if (formattedNumber.startsWith('0')) {
        formattedNumber = formattedNumber.substring(1);
      }
      formattedNumber = `${countryCode}${formattedNumber}`;
    }

    try {
      await api.post('/calls/outbound', { 
        agent_id: agentId || agents?.[0]?.id, 
        to_number: formattedNumber, 
        context: { source: 'dashboard' } 
      });
      setNumber('');
      setMessage('Call queued successfully.');
      await reload();
    } catch (err) {
      setMessage(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function simulate(id: string) {
    try {
      await api.post(`/calls/${id}/simulate`);
      setMessage('Mock call completed and summary queued.');
      await reload();
    } catch (err) {
      setMessage(errorMessage(err));
    }
  }

  async function fetchSummary(id: string) {
    setSelectedCallId(id);
    setSummary(null);
    setSummaryError('');
    setSummaryLoading(true);
    try {
      const res = await api.get(`/calls/${id}/summary`);
      setSummary(res.data);
    } catch (err) {
      setSummaryError(errorMessage(err));
    } finally {
      setSummaryLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title">Calls</h1>
        <p className="page-subtitle">Start, monitor, review, and audit inbound and outbound AI calls.</p>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>New outbound call</CardTitle>
          <CardDescription>Mock mode runs locally. Twilio mode places a real call using the same endpoint.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={create} className="grid gap-3 md:grid-cols-[1fr_1fr_auto]">
            <select className="h-10 rounded-md border bg-background px-3 text-sm" value={agentId} onChange={e => setAgentId(e.target.value)} required>
              <option value="">Select an agent</option>
              {agents?.filter(a => a.is_active).map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
            <div className="flex gap-2">
              <select 
                className="h-10 rounded-md border bg-background px-3 text-sm w-[100px]" 
                value={countryCode} 
                onChange={e => setCountryCode(e.target.value)}
              >
                <option value="+1">🇺🇸 +1</option>
                <option value="+44">🇬🇧 +44</option>
                <option value="+91">🇮🇳 +91</option>
                <option value="+61">🇦🇺 +61</option>
                <option value="+49">🇩🇪 +49</option>
                <option value="+33">🇫🇷 +33</option>
                <option value="+81">🇯🇵 +81</option>
                <option value="+86">🇨🇳 +86</option>
                <option value="+55">🇧🇷 +55</option>
              </select>
              <Input className="flex-1" value={number} onChange={e => setNumber(e.target.value)} placeholder="Phone number" required />
            </div>
            <Button disabled={busy || !agents?.length}>
              <PhoneCall className="mr-2 h-4 w-4" />{busy ? 'Queuing…' : 'Start call'}
            </Button>
          </form>
          {message && <p className="mt-3 text-sm text-muted-foreground">{message}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Call history</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? <p>Loading calls…</p> : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Number</TableHead>
                  <TableHead>Direction</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Revenue</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.items.map(call => (
                  <TableRow key={call.id}>
                    <TableCell className="font-medium">{call.direction === 'outbound' ? call.to_number : call.from_number}</TableCell>
                    <TableCell className="capitalize">{call.direction}</TableCell>
                    <TableCell><Badge>{call.status}</Badge></TableCell>
                    <TableCell>{duration(call.duration_seconds)}</TableCell>
                    <TableCell>{money(Number(call.revenue))}</TableCell>
                    <TableCell>{new Date(call.created_at).toLocaleString()}</TableCell>
                    <TableCell>
                      {call.status !== 'completed' && (
                        <Button size="sm" variant="outline" onClick={() => void simulate(call.id)}>
                          <Play className="mr-1.5 h-3.5 w-3.5" />Simulate
                        </Button>
                      )}
                      {call.status === 'completed' && (
                        <Button size="sm" variant="secondary" onClick={() => void fetchSummary(call.id)}>
                          <FileText className="mr-1.5 h-3.5 w-3.5" />Summary
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
                {!data?.items.length && (
                  <TableRow>
                    <TableCell colSpan={7} className="py-10 text-center text-muted-foreground">No calls found.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {selectedCallId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <CardHeader className="flex flex-row items-center justify-between sticky top-0 bg-card z-10 border-b pb-4">
              <CardTitle>Call Summary</CardTitle>
              <Button variant="ghost" size="icon" onClick={() => setSelectedCallId(null)}>
                <X className="h-5 w-5" />
              </Button>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              {summaryLoading && <p className="text-muted-foreground animate-pulse">Analyzing transcript and generating summary...</p>}
              {summaryError && <p className="text-destructive">{summaryError}</p>}
              {summary && (
                <>
                  <div className="flex gap-2 mb-4">
                    <Badge className="bg-primary/10 text-primary capitalize border">
                      Sentiment: {summary.sentiment}
                    </Badge>
                    <Badge className="bg-secondary text-secondary-foreground capitalize border">
                      Outcome: {summary.disposition}
                    </Badge>
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold mb-2">Summary</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">{summary.summary}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold mb-2">Key Points</h3>
                    <ul className="list-disc pl-5 text-sm text-muted-foreground space-y-1">
                      {summary.key_points?.map((pt, i) => <li key={i}>{pt}</li>)}
                    </ul>
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold mb-2">Action Items</h3>
                    <ul className="list-disc pl-5 text-sm text-muted-foreground space-y-1">
                      {summary.action_items?.length > 0 ? (
                        summary.action_items.map((act, i) => <li key={i}>{act}</li>)
                      ) : (
                        <li>No action items identified.</li>
                      )}
                    </ul>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
