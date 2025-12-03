'use client';

import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api-client';

interface HallucinationDetection {
  type: string;
  severity: 'high' | 'medium' | 'low';
  confidence: number;
  location: { start: number; end: number };
  description: string;
  suggestion: string;
}

interface HallucinationResult {
  text: string;
  hallucination_score: number;
  is_hallucination: boolean;
  detections: HallucinationDetection[];
  analysis_time: number;
  metadata: {
    model_version: string;
    confidence_threshold: number;
  };
}

export function HallucinationDetector() {
  const [inputText, setInputText] = useState('');
  const [context, setContext] = useState('');
  const [lastResult, setLastResult] = useState<HallucinationResult | null>(null);

  // Query for hallucination stats
  const { data: stats } = useQuery({
    queryKey: ['hallucination-stats'],
    queryFn: api.getHallucinationStats,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Mutation for detecting hallucinations
  const detectMutation = useMutation({
    mutationFn: api.detectHallucinations,
    onSuccess: (data) => {
      setLastResult(data);
    },
  });

  const handleDetect = () => {
    if (!inputText.trim()) return;
    
    detectMutation.mutate({
      text: inputText,
      context: context.trim() || undefined,
    });
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const highlightText = (text: string, detections: HallucinationDetection[]) => {
    if (!detections.length) return text;

    let result = text;
    let offset = 0;

    detections
      .sort((a, b) => a.location.start - b.location.start)
      .forEach((detection) => {
        const start = detection.location.start + offset;
        const end = detection.location.end + offset;
        const originalText = result.substring(start, end);
        const highlightedText = `<span class="bg-red-200 px-1 rounded" title="${detection.description}">${originalText}</span>`;
        
        result = result.substring(0, start) + highlightedText + result.substring(end);
        offset += highlightedText.length - originalText.length;
      });

    return result;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Hallucination Detection</h2>
        <p className="text-gray-600 mt-1">
          Analyze text for potential hallucinations, factual inconsistencies, and logical errors
        </p>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="text-sm font-medium text-gray-500">Total Analyzed</div>
            <div className="text-2xl font-bold text-gray-900">{stats.total_analyzed.toLocaleString()}</div>
          </Card>
          <Card className="p-4">
            <div className="text-sm font-medium text-gray-500">Hallucinations Detected</div>
            <div className="text-2xl font-bold text-red-600">{stats.hallucinations_detected.toLocaleString()}</div>
          </Card>
          <Card className="p-4">
            <div className="text-sm font-medium text-gray-500">Detection Rate</div>
            <div className="text-2xl font-bold text-orange-600">{(stats.detection_rate * 100).toFixed(2)}%</div>
          </Card>
          <Card className="p-4">
            <div className="text-sm font-medium text-gray-500">Last 24h</div>
            <div className="text-2xl font-bold text-blue-600">{stats.recent_trends.last_24h}</div>
          </Card>
        </div>
      )}

      {/* Input Section */}
      <Card className="p-6">
        <div className="space-y-4">
          <div>
            <label htmlFor="text-input" className="block text-sm font-medium text-gray-700">
              Text to Analyze
            </label>
            <Textarea
              id="text-input"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Enter the text you want to analyze for hallucinations..."
              className="mt-1"
              rows={6}
            />
          </div>
          
          <div>
            <label htmlFor="context-input" className="block text-sm font-medium text-gray-700">
              Context (Optional)
            </label>
            <Textarea
              id="context-input"
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="Provide additional context to improve detection accuracy..."
              className="mt-1"
              rows={3}
            />
          </div>

          <Button
            onClick={handleDetect}
            disabled={!inputText.trim() || detectMutation.isPending}
            className="w-full"
          >
            {detectMutation.isPending ? 'Analyzing...' : 'Detect Hallucinations'}
          </Button>
        </div>
      </Card>

      {/* Results Section */}
      {lastResult && (
        <Card className="p-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Analysis Results</h3>
              <div className="flex items-center space-x-2">
                <Badge variant={lastResult.is_hallucination ? 'destructive' : 'default'}>
                  {lastResult.is_hallucination ? 'Hallucination Detected' : 'No Hallucination'}
                </Badge>
                <span className="text-sm text-gray-500">
                  Score: {(lastResult.hallucination_score * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            {/* Highlighted Text */}
            <div className="border rounded-lg p-4 bg-gray-50">
              <h4 className="font-medium mb-2">Analyzed Text:</h4>
              <div 
                className="text-sm leading-relaxed"
                dangerouslySetInnerHTML={{
                  __html: highlightText(lastResult.text, lastResult.detections)
                }}
              />
            </div>

            {/* Detections */}
            {lastResult.detections.length > 0 && (
              <div>
                <h4 className="font-medium mb-3">Detected Issues ({lastResult.detections.length})</h4>
                <div className="space-y-3">
                  {lastResult.detections.map((detection, index) => (
                    <div key={index} className="border rounded-lg p-4 bg-white">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <Badge className={getSeverityColor(detection.severity)}>
                            {detection.severity.toUpperCase()}
                          </Badge>
                          <span className="font-medium capitalize">
                            {detection.type.replace('_', ' ')}
                          </span>
                        </div>
                        <span className="text-sm text-gray-500">
                          {(detection.confidence * 100).toFixed(1)}% confidence
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 mb-2">{detection.description}</p>
                      <p className="text-sm text-blue-600 italic">{detection.suggestion}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="text-xs text-gray-500 pt-4 border-t">
              Analysis completed in {lastResult.analysis_time}ms • 
              Model: {lastResult.metadata.model_version} • 
              Threshold: {(lastResult.metadata.confidence_threshold * 100)}%
            </div>
          </div>
        </Card>
      )}

      {/* Error Display */}
      {detectMutation.isError && (
        <Card className="p-4 bg-red-50 border-red-200">
          <div className="text-red-800">
            Error: {detectMutation.error?.message || 'Failed to analyze text'}
          </div>
        </Card>
      )}
    </div>
  );
}