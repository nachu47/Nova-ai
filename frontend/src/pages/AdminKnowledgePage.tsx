import { Brain, FileText, Database } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';

export function AdminKnowledgePage() {
    const { user } = useAuth();

    if (user?.role !== 'superadmin') return <p className="text-destructive">Administrator access is required.</p>;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="page-title">Knowledge & RAG Engine</h1>
                <p className="page-subtitle">Global semantic index, vector embeddings, and RAG document storage status.</p>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
                <Card>
                    <CardContent className="p-5 flex items-center gap-3">
                        <Brain className="h-6 w-6 text-primary" />
                        <div>
                            <p className="text-xl font-bold">OpenAI Embedding 3</p>
                            <p className="text-xs text-muted-foreground">Active Vector Model</p>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-5 flex items-center gap-3">
                        <FileText className="h-6 w-6 text-emerald-500" />
                        <div>
                            <p className="text-xl font-bold">Semantic Search</p>
                            <p className="text-xs text-muted-foreground">Enabled Platform-Wide</p>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-5 flex items-center gap-3">
                        <Database className="h-6 w-6 text-purple-500" />
                        <div>
                            <p className="text-xl font-bold">PostgreSQL Vector</p>
                            <p className="text-xs text-muted-foreground">Storage Backend</p>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>RAG Vector Store & Document Isolation</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-muted-foreground py-6 text-center">
                        All uploaded Knowledge Base documents and vector embeddings are partitioned by tenant <code className="bg-muted px-1.5 py-0.5 rounded">organization_id</code> to guarantee zero cross-company data leakage during voice AI call retrieval.
                    </p>
                </CardContent>
            </Card>
        </div>
    );
}
