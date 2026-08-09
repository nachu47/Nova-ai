import { useEffect, useState, type FormEvent } from 'react';
import { Save, Key, Phone, Shield } from 'lucide-react';
import { getSettings, updateSetting, errorMessage } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

export function ProviderSettings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [twilioSid, setTwilioSid] = useState('');
  const [twilioToken, setTwilioToken] = useState('');
  const [twilioPhone, setTwilioPhone] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const data = await getSettings();
        if (data.twilio_account_sid) setTwilioSid(data.twilio_account_sid);
        if (data.twilio_auth_token) setTwilioToken(data.twilio_auth_token.secret || '');
        if (data.twilio_phone_number) setTwilioPhone(data.twilio_phone_number);
        if (data.openai_api_key) setOpenaiKey(data.openai_api_key.secret || '');
      } catch (err) {
        setError(errorMessage(err));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setSaving(true);
    
    try {
      await updateSetting('twilio_account_sid', twilioSid, false);
      await updateSetting('twilio_auth_token', { secret: twilioToken }, true);
      await updateSetting('twilio_phone_number', twilioPhone, false);
      await updateSetting('openai_api_key', { secret: openaiKey }, true);
      
      setSuccess('Provider settings saved successfully!');
      
      const data = await getSettings();
      if (data.twilio_auth_token) setTwilioToken(data.twilio_auth_token.secret || '');
      if (data.openai_api_key) setOpenaiKey(data.openai_api_key.secret || '');
      
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-4 text-muted-foreground">Loading provider settings...</div>;
  }

  return (
    <Card className="border-purple-100 bg-white/60 backdrop-blur-xl shadow-sm">
      <CardHeader>
        <CardTitle className="text-xl flex items-center gap-2">
          <Shield className="w-5 h-5 text-purple-600" />
          API Providers
        </CardTitle>
        <CardDescription>Configure external API keys for Twilio and OpenAI</CardDescription>
      </CardHeader>
      
      <CardContent>
        {error && (
          <div className="mb-6 p-4 bg-red-50 text-red-600 rounded-xl border border-red-100 text-sm">
            {error}
          </div>
        )}
        
        {success && (
          <div className="mb-6 p-4 bg-green-50 text-green-600 rounded-xl border border-green-100 text-sm">
            {success}
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-6">
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-900 border-b pb-2 flex items-center gap-2">
              <Phone className="w-4 h-4 text-red-500" /> Twilio
            </h3>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Account SID</label>
                <input
                  type="text"
                  value={twilioSid}
                  onChange={(e) => setTwilioSid(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-200 rounded-lg bg-white/50 text-sm"
                  placeholder="AC..."
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Default Outbound Phone Number</label>
                <input
                  type="text"
                  value={twilioPhone}
                  onChange={(e) => setTwilioPhone(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-200 rounded-lg bg-white/50 text-sm"
                  placeholder="+1234567890"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-medium text-gray-700 mb-1">Auth Token (Encrypted)</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Key className="h-3 w-3 text-gray-400" />
                  </div>
                  <input
                    type="password"
                    value={twilioToken}
                    onChange={(e) => setTwilioToken(e.target.value)}
                    className="block w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg bg-white/50 text-sm"
                    placeholder="Encrypted & hidden"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-4 pt-2">
            <h3 className="text-sm font-semibold text-gray-900 border-b pb-2 flex items-center gap-2">
              <Shield className="w-4 h-4 text-emerald-500" /> OpenAI
            </h3>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">API Key (Encrypted)</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Key className="h-3 w-3 text-gray-400" />
                </div>
                <input
                  type="password"
                  value={openaiKey}
                  onChange={(e) => setOpenaiKey(e.target.value)}
                  className="block w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg bg-white/50 text-sm"
                  placeholder="sk-..."
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-4">
            <Button
              type="submit"
              disabled={saving}
              className="bg-purple-600 hover:bg-purple-700 text-white rounded-lg shadow-sm"
            >
              <Save className="w-4 h-4 mr-2" />
              {saving ? 'Saving...' : 'Save Keys'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
