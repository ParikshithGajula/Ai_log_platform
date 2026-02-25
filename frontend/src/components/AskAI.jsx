import React, { useState } from 'react';
import { askAI } from '../api/client';

/**
 * Key React Concept: SSE streaming — instead of waiting for the full response,
 * we display tokens as they arrive, like watching someone type.
 */
export default function AskAI() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  // const [tokens, setTokens] = useState([]);

  const handleAsk = async () => {
    if (!query.trim()) return;

    setIsStreaming(true);
    setResponse('');

    const tokenBuffer = [];

    await askAI(
      query,
      [],
      (token) => {
        tokenBuffer.push(token);
        setResponse(tokenBuffer.join(''));
      },
      (result) => {
        setIsStreaming(false);
        if (result.error) {
          setResponse(`Error: ${result.error}`);
        } else {
          // Parse structured response if available
          if (typeof result === 'object') {
            setResponse(JSON.stringify(result, null, 2));
          } else {
            setResponse(result);
          }
        }
      }
    );
  };

  const handleClear = () => {
    setQuery('');
    setResponse('');
  };

  // Parse response as structured data if possible
  const parseResponse = (text) => {
    if (!text) return null;
    try {
      return JSON.parse(text);
    } catch {
      return null;
    }
  };

  const parsed = parseResponse(response);

  return (
    <div className="space-y-4">
      <div className="bg-surface border border-border rounded-lg p-6">
        <label className="block text-sm font-semibold mb-3 text-text">
          Ask AI About Your Logs
        </label>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={isStreaming}
          placeholder="Why is the payment service throwing errors?"
          rows="4"
          className="w-full px-4 py-3 bg-[#161b22] text-text border border-border rounded resize-none disabled:opacity-50"
        />

        <div className="flex gap-3 mt-4">
          <button
            onClick={handleAsk}
            disabled={!query.trim() || isStreaming}
            className="flex-1 px-6 py-2 bg-accent text-surface font-semibold rounded hover:opacity-90 disabled:opacity-50 transition"
          >
            {isStreaming ? 'Analyzing...' : 'Ask AI'}
          </button>
          <button
            onClick={handleClear}
            className="px-6 py-2 bg-[#161b22] text-text border border-border rounded hover:border-accent transition"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Streaming indicator */}
      {isStreaming && (
        <div className="flex items-center gap-2 text-accent text-sm">
          <span>Thinking</span>
          <span className="inline-flex gap-1">
            <span className="inline-block w-1 h-1 bg-accent rounded-full animate-bounce"></span>
            <span className="inline-block w-1 h-1 bg-accent rounded-full animate-bounce delay-100"></span>
            <span className="inline-block w-1 h-1 bg-accent rounded-full animate-bounce delay-200"></span>
          </span>
        </div>
      )}

      {/* Response box */}
      {response && (
        <div className="bg-surface border border-border rounded-lg p-6">
          <h3 className="text-sm font-semibold mb-4 text-text">Response</h3>

          {parsed ? (
            <div className="space-y-4 text-sm">
              {parsed.cause && (
                <div>
                  <span className="font-bold text-accent">Root Cause:</span>{' '}
                  <span className="text-text">{parsed.cause}</span>
                </div>
              )}

              {parsed.confidence && (
                <div>
                  <span className="font-semibold text-text">Confidence:</span>
                  <span
                    className={`ml-2 px-2 py-1 rounded text-xs font-semibold ${parsed.confidence === 'HIGH'
                        ? 'bg-green-900 text-green-200'
                        : parsed.confidence === 'MEDIUM'
                          ? 'bg-yellow-900 text-yellow-200'
                          : 'bg-red-900 text-red-200'
                      }`}
                  >
                    {parsed.confidence}
                  </span>
                </div>
              )}

              {parsed.severity && (
                <div>
                  <span className="font-semibold text-text">Severity:</span>
                  <span
                    className={`ml-2 px-2 py-1 rounded text-xs font-semibold ${parsed.severity === 'CRITICAL'
                        ? 'bg-red-900 text-red-200'
                        : parsed.severity === 'HIGH'
                          ? 'bg-orange-900 text-orange-200'
                          : 'bg-yellow-900 text-yellow-200'
                      }`}
                  >
                    {parsed.severity}
                  </span>
                </div>
              )}

              {parsed.affected_services && Array.isArray(parsed.affected_services) && (
                <div>
                  <span className="font-semibold text-text">Affected Services:</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {parsed.affected_services.map((service, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-[#161b22] text-accent rounded text-xs border border-border"
                      >
                        {service}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {parsed.recommendation && (
                <div>
                  <span className="font-semibold text-text">Recommendation:</span>
                  <p className="text-text italic mt-1">{parsed.recommendation}</p>
                </div>
              )}

              {parsed.impact && (
                <div>
                  <span className="font-semibold text-text">Impact:</span>
                  <p className="text-text mt-1">{parsed.impact}</p>
                </div>
              )}

              {parsed.solution && (
                <div>
                  <span className="font-semibold text-text">Solution:</span>
                  <p className="text-text mt-1">{parsed.solution}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-text whitespace-pre-wrap font-mono text-xs overflow-auto max-h-64">
              {response}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
