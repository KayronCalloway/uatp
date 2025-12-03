'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/auth-context-simple';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { isValidApiKey } from '@/lib/utils';
import { KeyRound, Loader2, AlertCircle } from 'lucide-react';

export function LoginForm() {
  const { login, isLoading } = useAuth();
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (!apiKey.trim()) {
      setError('Please enter your API key');
      return;
    }

    if (!isValidApiKey(apiKey)) {
      setError('Invalid API key format');
      return;
    }

    setIsSubmitting(true);
    
    try {
      const success = await login(apiKey);
      if (!success) {
        setError('Invalid API key or connection failed');
      }
    } catch (err) {
      setError('Authentication failed. Please check your API key and try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <div className="flex items-center justify-center mb-4">
            <KeyRound className="h-12 w-12 text-blue-600" />
          </div>
          <CardTitle className="text-2xl font-bold text-center">
            UATP Capsule Engine
          </CardTitle>
          <CardDescription className="text-center">
            Enter your API key to access the dashboard
          </CardDescription>
        </CardHeader>
        
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Input
                type="password"
                placeholder="Enter your API key"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                disabled={isSubmitting}
                className="w-full"
                autoComplete="current-password"
              />
              {error && (
                <div className="flex items-center space-x-2 text-sm text-red-600">
                  <AlertCircle className="h-4 w-4" />
                  <span>{error}</span>
                </div>
              )}
            </div>
            
            <div className="text-sm text-gray-600">
              <p>Don&apos;t have an API key? Contact your administrator or check the documentation.</p>
            </div>
          </CardContent>
          
          <CardFooter>
            <Button
              type="submit"
              disabled={isSubmitting || !apiKey.trim()}
              className="w-full"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Authenticating...
                </>
              ) : (
                'Sign In'
              )}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}