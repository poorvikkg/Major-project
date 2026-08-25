import { useState, useEffect } from 'react';

/* ---------- Loading Dots ---------- */
const loadingPhrases = [
  'Searching police records…',
  'Analyzing FIRs…',
  'Finding similar cases…',
  'Comparing crime patterns…',
  'Building response…',
];

function RagLoadingState() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setIndex((prev) => (prev + 1) % loadingPhrases.length);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="rag-loading">
      <span className="rag-dot" style={{ animationDelay: '0s' }} />
      <span className="rag-dot" style={{ animationDelay: '0.2s' }} />
      <span className="rag-dot" style={{ animationDelay: '0.4s' }} />
      <span className="rag-loading-text">{loadingPhrases[index]}</span>
    </div>
  );
}

/* ---------- Response Card ---------- */
function RagResponseCard({ message }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rag-response-card">
      {/* Answer */}
      <div className="rag-response-text">{message.content}</div>

      {/* Metadata grid */}
      {(message.confidence !== undefined || message.sources?.length > 0 || message.supportingCases?.length > 0) && (
        <div className="rag-metadata-grid">
          {/* Confidence */}
          {message.confidence !== undefined && (
            <div className="rag-meta-block">
              <h4 className="rag-meta-label">Confidence</h4>
              <div className="rag-confidence-bar-wrap">
                <div className="rag-confidence-track">
                  <div
                    className={`rag-confidence-fill ${
                      message.confidence >= 0.8
                        ? 'rag-confidence-high'
                        : message.confidence >= 0.5
                        ? 'rag-confidence-mid'
                        : 'rag-confidence-low'
                    }`}
                    style={{ width: `${message.confidence * 100}%` }}
                  />
                </div>
                <span className="rag-confidence-value">{Math.round(message.confidence * 100)}%</span>
              </div>
            </div>
          )}

          {/* Sources */}
          {message.sources?.length > 0 && (
            <div className="rag-meta-block">
              <h4 className="rag-meta-label">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                Sources
              </h4>
              <ul className="rag-source-list">
                {message.sources.map((src, idx) => (
                  <li key={idx} className="rag-source-item">{src}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Supporting Cases */}
          {message.supportingCases?.length > 0 && (
            <div className="rag-meta-block">
              <h4 className="rag-meta-label">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                Supporting Cases
              </h4>
              <div className="rag-case-tags">
                {message.supportingCases.map((caseId, idx) => (
                  <span key={idx} className="rag-case-tag">Case {caseId}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Quick actions */}
      <div className="rag-actions">
        <button className="rag-action-btn" onClick={handleCopy} title="Copy">
          {copied ? '✓ Copied' : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          )}
        </button>
        <button className="rag-action-btn" title="Helpful">👍</button>
        <button className="rag-action-btn" title="Not Helpful">👎</button>
      </div>

      {/* Suggested follow-ups */}
      {message.suggestedFollowUps?.length > 0 && (
        <div className="rag-followups">
          <h4 className="rag-meta-label">Suggested Questions</h4>
          <div className="rag-followup-list">
            {message.suggestedFollowUps.map((q, idx) => (
              <button key={idx} className="rag-followup-btn">{q}</button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------- Message Bubble ---------- */
export default function RagMessageBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`rag-bubble ${isUser ? 'rag-bubble-user' : 'rag-bubble-assistant'}`}>
      <div className="rag-bubble-inner">
        {/* Avatar */}
        <div className={`rag-avatar ${isUser ? 'rag-avatar-user' : 'rag-avatar-bot'}`}>
          {isUser ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5" fill="currentColor" stroke="none"/><circle cx="15.5" cy="8.5" r="1.5" fill="currentColor" stroke="none"/><path d="M9 15c.83.67 1.83 1 3 1s2.17-.33 3-1"/></svg>
          )}
        </div>

        {/* Content */}
        <div className="rag-bubble-content">
          {message.isLoading ? (
            <RagLoadingState />
          ) : isUser ? (
            <div className="rag-user-text">{message.content}</div>
          ) : (
            <RagResponseCard message={message} />
          )}
        </div>
      </div>
    </div>
  );
}
