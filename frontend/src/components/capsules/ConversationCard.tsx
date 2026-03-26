'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  MessageSquare,
  User,
  Bot,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  Clock,
  Zap,
  AlertCircle,
  Code,
  FileText
} from 'lucide-react';
import { useState, useMemo } from 'react';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
  token_count?: number;
  model_info?: string;
  confidence?: number;
  measurements?: Record<string, any>;
  step_type?: string;
  step_id?: number;
  uncertainty_sources?: string[];
  confidence_explanation?: {
    boosting_factors?: string[];
    limiting_factors?: string[];
    improvement_suggestions?: string[];
  };
}

interface ConversationCardProps {
  payload: any;
}

// Code block detection and rendering
function renderContent(content: string) {
  // Check for code blocks
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
  const parts: Array<{ type: 'text' | 'code'; content: string; language?: string }> = [];
  let lastIndex = 0;
  let match;

  while ((match = codeBlockRegex.exec(content)) !== null) {
    // Add text before code block
    if (match.index > lastIndex) {
      parts.push({
        type: 'text',
        content: content.slice(lastIndex, match.index)
      });
    }

    // Add code block
    parts.push({
      type: 'code',
      content: match[2],
      language: match[1] || 'plaintext'
    });

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < content.length) {
    parts.push({
      type: 'text',
      content: content.slice(lastIndex)
    });
  }

  if (parts.length === 0) {
    return <span className="whitespace-pre-wrap">{content}</span>;
  }

  return (
    <div className="space-y-2">
      {parts.map((part, i) =>
        part.type === 'code' ? (
          <div key={i} className="relative group">
            <div className="flex items-center justify-between bg-gray-800 text-gray-300 px-3 py-1 rounded-t text-xs">
              <span className="flex items-center gap-1">
                <Code className="h-3 w-3" />
                {part.language}
              </span>
            </div>
            <pre className="bg-gray-900 text-gray-100 p-3 rounded-b overflow-x-auto text-sm">
              <code>{part.content}</code>
            </pre>
          </div>
        ) : (
          <span key={i} className="whitespace-pre-wrap">{part.content}</span>
        )
      )}
    </div>
  );
}

function MessageItem({ message, index, isExpanded, onToggle }: {
  message: Message;
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isLongContent = message.content.length > 500;
  const displayContent = isExpanded || !isLongContent
    ? message.content
    : message.content.slice(0, 500) + '...';

  const roleConfig = {
    user: {
      bg: 'bg-gradient-to-r from-blue-50 to-blue-100',
      border: 'border-blue-200',
      iconBg: 'bg-blue-500',
      textColor: 'text-blue-900',
      label: 'User',
      icon: User
    },
    assistant: {
      bg: 'bg-gradient-to-r from-purple-50 to-indigo-50',
      border: 'border-purple-200',
      iconBg: 'bg-purple-600',
      textColor: 'text-purple-900',
      label: 'Claude',
      icon: Bot
    },
    system: {
      bg: 'bg-gradient-to-r from-yellow-50 to-orange-50',
      border: 'border-yellow-200',
      iconBg: 'bg-yellow-500',
      textColor: 'text-yellow-900',
      label: 'System',
      icon: AlertCircle
    }
  };

  const config = roleConfig[message.role] || roleConfig.system;
  const Icon = config.icon;

  return (
    <div
      className={`rounded-xl border-2 ${config.border} ${config.bg} overflow-hidden transition-all duration-200 hover:shadow-md`}
    >
      {/* Message Header - Always visible */}
      <div
        className="flex items-center justify-between px-4 py-3 cursor-pointer"
        onClick={onToggle}
      >
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-full ${config.iconBg} flex items-center justify-center shadow-sm`}>
            <Icon className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className={`font-semibold ${config.textColor}`}>
                {config.label}
              </span>
              {message.step_id && (
                <span className="text-xs bg-white/50 px-2 py-0.5 rounded">
                  Step {message.step_id}
                </span>
              )}
              {message.confidence !== undefined && (
                <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                  message.confidence >= 0.8 ? 'bg-green-100 text-green-700' :
                  message.confidence >= 0.6 ? 'bg-blue-100 text-blue-700' :
                  message.confidence >= 0.4 ? 'bg-yellow-100 text-yellow-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {(message.confidence * 100).toFixed(0)}% confident
                </span>
              )}
            </div>
            <div className="flex items-center gap-3 text-xs text-gray-500 mt-0.5">
              {message.timestamp && (
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {new Date(message.timestamp).toLocaleString()}
                </span>
              )}
              {message.token_count && (
                <span className="flex items-center gap-1">
                  <Zap className="h-3 w-3" />
                  ~{message.token_count} tokens
                </span>
              )}
              {message.model_info && (
                <span className="bg-gray-200 px-1.5 py-0.5 rounded text-xs">
                  {message.model_info}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => { e.stopPropagation(); handleCopy(); }}
            className="h-8 w-8 p-0"
          >
            {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
          </Button>
          <div className="text-gray-400">
            {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
          </div>
        </div>
      </div>

      {/* Message Content - Collapsible */}
      <div className={`px-4 pb-4 transition-all duration-200 ${isExpanded ? 'block' : 'block'}`}>
        <div className="pl-[52px]">
          {/* Main Content */}
          <div className="text-sm text-gray-800 leading-relaxed">
            {renderContent(displayContent)}
          </div>

          {/* Show more/less for long content */}
          {isLongContent && (
            <button
              onClick={(e) => { e.stopPropagation(); onToggle(); }}
              className="mt-2 text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              {isExpanded ? 'Show less' : `Show more (${message.content.length} characters)`}
            </button>
          )}

          {/* Expanded Details */}
          {isExpanded && (
            <div className="mt-4 space-y-3 border-t pt-3">
              {/* Confidence Explanation */}
              {message.confidence_explanation && (
                <div className="bg-white/50 rounded-lg p-3 space-y-2">
                  <div className="text-xs font-semibold text-gray-700">Confidence Analysis</div>

                  {(message.confidence_explanation.boosting_factors?.length ?? 0) > 0 && (
                    <div>
                      <div className="text-xs text-green-700 font-medium">Boosting Factors:</div>
                      <ul className="text-xs text-green-600 space-y-0.5 ml-3">
                        {(message.confidence_explanation.boosting_factors ?? []).map((f, i) => (
                          <li key={i}>+ {f}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {(message.confidence_explanation.limiting_factors?.length ?? 0) > 0 && (
                    <div>
                      <div className="text-xs text-red-700 font-medium">Limiting Factors:</div>
                      <ul className="text-xs text-red-600 space-y-0.5 ml-3">
                        {(message.confidence_explanation.limiting_factors ?? []).map((f, i) => (
                          <li key={i}>- {f}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {(message.confidence_explanation.improvement_suggestions?.length ?? 0) > 0 && (
                    <div>
                      <div className="text-xs text-blue-700 font-medium">Suggestions:</div>
                      <ul className="text-xs text-blue-600 space-y-0.5 ml-3">
                        {(message.confidence_explanation.improvement_suggestions ?? []).map((s, i) => (
                          <li key={i}>* {s}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Uncertainty Sources */}
              {message.uncertainty_sources && message.uncertainty_sources.length > 0 && (
                <div className="bg-yellow-50 rounded-lg p-3">
                  <div className="text-xs font-semibold text-yellow-800 mb-1">Uncertainty Sources</div>
                  <ul className="text-xs text-yellow-700 space-y-0.5">
                    {message.uncertainty_sources.map((s, i) => (
                      <li key={i} className="flex items-start gap-1">
                        <AlertCircle className="h-3 w-3 mt-0.5 flex-shrink-0" />
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Raw Measurements */}
              {message.measurements && Object.keys(message.measurements).length > 0 && (
                <details className="text-xs">
                  <summary className="cursor-pointer text-gray-600 hover:text-gray-900 font-medium">
                    View Measurements ({Object.keys(message.measurements).length})
                  </summary>
                  <pre className="mt-2 bg-gray-100 p-2 rounded overflow-x-auto text-xs">
                    {JSON.stringify(message.measurements, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function ConversationCard({ payload }: ConversationCardProps) {
  const [expandedMessages, setExpandedMessages] = useState<Set<number>>(new Set([0])); // First message expanded by default
  const [showAll, setShowAll] = useState(false);

  // Extract messages from various payload structures
  const messages = useMemo((): Message[] => {
    if (!payload) return [];

    // Check reasoning_steps first (most common for Claude Code captures)
    if (payload.reasoning_steps && Array.isArray(payload.reasoning_steps)) {
      return payload.reasoning_steps.map((step: any, i: number) => ({
        // NEW: Use explicit role field first, fall back to inference
        role: step.role ||
              (step.step_type?.includes('user') ? 'user' :
               step.step_type?.includes('assistant') ? 'assistant' :
               (step.attribution_sources?.[0]?.startsWith('user') ? 'user' : 'assistant')),
        content: step.content || step.reasoning || step.text || JSON.stringify(step),
        timestamp: step.timestamp,
        token_count: step.token_count || step.measurements?.message_index,
        model_info: step.attribution_sources?.[0]?.replace(/^(user|assistant):/, '') || step.model,
        confidence: step.confidence,
        measurements: step.measurements,
        step_id: step.step_id || i + 1,
        step_type: step.step_type,
        uncertainty_sources: step.uncertainty_sources,
        confidence_explanation: step.measurements?.confidence_explanation
      }));
    }

    // Direct messages array
    if (payload.messages && Array.isArray(payload.messages)) {
      return payload.messages;
    }

    // Nested locations
    const nestedPaths = [
      payload.content?.messages,
      payload.trace?.messages,
      payload.session_messages,
      payload.content?.data?.messages
    ];

    for (const path of nestedPaths) {
      if (path && Array.isArray(path)) return path;
    }

    // User query / assistant response pattern
    if (payload.user_query || payload.assistant_response) {
      const msgs: Message[] = [];
      if (payload.user_query) {
        msgs.push({ role: 'user', content: payload.user_query });
      }
      if (payload.assistant_response) {
        msgs.push({ role: 'assistant', content: payload.assistant_response });
      }
      return msgs;
    }

    // Session metadata user goal as fallback
    if (payload.session_metadata?.user_goal) {
      const msgs: Message[] = [{
        role: 'user',
        content: payload.session_metadata.user_goal
      }];

      if (payload.plain_language_summary?.decision) {
        msgs.push({
          role: 'assistant',
          content: payload.plain_language_summary.decision +
            (payload.plain_language_summary.why ? `\n\n**Why:** ${payload.plain_language_summary.why}` : '')
        });
      }

      return msgs;
    }

    return [];
  }, [payload]);

  const toggleMessage = (index: number) => {
    setExpandedMessages(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const expandAll = () => {
    setExpandedMessages(new Set(messages.map((_, i) => i)));
    setShowAll(true);
  };

  const collapseAll = () => {
    setExpandedMessages(new Set());
    setShowAll(false);
  };

  if (messages.length === 0) {
    return null;
  }

  const userCount = messages.filter(m => m.role === 'user').length;
  const assistantCount = messages.filter(m => m.role === 'assistant').length;
  const totalTokens = messages.reduce((sum, m) => sum + (m.token_count || 0), 0);

  return (
    <Card className="overflow-hidden">
      <CardHeader className="bg-gradient-to-r from-blue-600 to-purple-600 text-white pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
              <MessageSquare className="h-5 w-5" />
            </div>
            <div>
              <span className="text-lg">Conversation</span>
              <div className="text-xs font-normal text-white/80 mt-0.5">
                {userCount} user, {assistantCount} assistant
                {totalTokens > 0 && ` | ~${totalTokens} tokens`}
              </div>
            </div>
          </CardTitle>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={showAll ? collapseAll : expandAll}
              className="text-white hover:bg-white/20"
            >
              {showAll ? 'Collapse All' : 'Expand All'}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-4 space-y-4 bg-gray-50">
        {messages.map((message, index) => (
          <MessageItem
            key={index}
            message={message}
            index={index}
            isExpanded={expandedMessages.has(index)}
            onToggle={() => toggleMessage(index)}
          />
        ))}

        {messages.length === 1 && !payload.messages && !payload.reasoning_steps && (
          <div className="text-xs text-gray-500 italic text-center pt-2 border-t">
            Note: Full conversation may not have been captured. Showing available content.
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default ConversationCard;
