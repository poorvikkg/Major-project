import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import RagChatInput from '../components/rag/RagChatInput';
import RagMessageBubble from '../components/rag/RagMessageBubble';

const RAG_API_URL = 'http://localhost:8001';

const suggestions = [
  'Show robbery cases in Bangalore',
  'Find unsolved murder cases',
  'Compare this FIR with previous cases',
  'Crime trends in Karnataka',
];

/* ---------- RAG Chat Page ---------- */
export default function RagChatPage() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => crypto.randomUUID());
  const messagesEndRef = useRef(null);

  // Drag & drop state
  const [isDragging, setIsDragging] = useState(false);
  const [uploadToast, setUploadToast] = useState('');
  const [globalUploading, setGlobalUploading] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  /* --- Send Message --- */
  const sendMessage = useCallback(
    async (content) => {
      if (!content.trim()) return;

      const userMsg = { id: crypto.randomUUID(), role: 'user', content };
      const placeholderId = crypto.randomUUID();
      const loadingMsg = { id: placeholderId, role: 'assistant', content: '', isLoading: true };

      setMessages((prev) => [...prev, userMsg, loadingMsg]);
      setIsLoading(true);

      try {
        const res = await fetch(`${RAG_API_URL}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: content, session_id: sessionId }),
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === placeholderId
              ? {
                  ...msg,
                  content: data.answer,
                  confidence: data.confidence,
                  sources: data.sources,
                  supportingCases: data.supporting_cases,
                  relatedCases: data.related_cases,
                  suggestedFollowUps: data.suggested_follow_ups,
                  isLoading: false,
                }
              : msg,
          ),
        );
      } catch (error) {
        console.error(error);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === placeholderId
              ? { ...msg, content: 'Sorry, I encountered an error while processing your request.', isLoading: false }
              : msg,
          ),
        );
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId],
  );

  /* --- File Upload (button) --- */
  const handleFileUpload = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${RAG_API_URL}/upload`, { method: 'POST', body: formData });
    if (!res.ok) throw new Error(`Upload failed: HTTP ${res.status}`);
    return res.json();
  };

  /* --- Drag & Drop --- */
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };
  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };
  const handleDrop = async (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files?.[0];
    if (!droppedFile || !droppedFile.name.endsWith('.pdf')) {
      alert('Only PDF files are supported.');
      return;
    }
    setGlobalUploading(true);
    setUploadToast('Uploading…');
    try {
      const data = await handleFileUpload(droppedFile);
      setUploadToast(data.message || 'Processing in background…');
      setTimeout(() => setUploadToast(''), 4000);
    } catch {
      setUploadToast('Failed to upload.');
      setTimeout(() => setUploadToast(''), 4000);
    } finally {
      setGlobalUploading(false);
    }
  };

  /* ---------- Render ---------- */
  return (
    <div
      className="rag-chat-page"
      id="rag-chat-page"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Header bar */}
      <header className="rag-chat-header">
        <button className="rag-back-btn" onClick={() => navigate(-1)} aria-label="Go back">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="19" y1="12" x2="5" y2="12" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
        </button>
        <div className="rag-header-info">
          <h1 className="rag-header-title">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
            Police Case Intelligence
          </h1>
          <span className="rag-header-subtitle">RAG-powered Investigation Assistant</span>
        </div>
        <button
          className="rag-clear-btn"
          onClick={() => setMessages([])}
          disabled={messages.length === 0}
          title="Clear chat"
        >
          Clear
        </button>
      </header>

      {/* Drag overlay */}
      {isDragging && (
        <div className="rag-drag-overlay">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          <h2>Drop PDF here</h2>
          <p>Upload and analyze instantly</p>
        </div>
      )}

      {/* Upload toast */}
      {uploadToast && (
        <div className="rag-upload-toast">
          {globalUploading && <span className="rag-toast-dot" />}
          {uploadToast}
        </div>
      )}

      {/* Messages or Empty State */}
      {messages.length === 0 ? (
        <div className="rag-empty-state">
          <div className="rag-empty-icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </div>
          <h2 className="rag-empty-title">Police Case Intelligence Assistant</h2>
          <p className="rag-empty-desc">
            Search cases, analyze FIRs, discover crime patterns, and ask questions using natural language.
          </p>
          <div className="rag-suggestions">
            {suggestions.map((s, idx) => (
              <button key={idx} className="rag-suggestion-btn" onClick={() => sendMessage(s)}>
                {s}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="rag-messages-area">
          {messages.map((msg) => (
            <RagMessageBubble key={msg.id} message={msg} />
          ))}
          <div ref={messagesEndRef} />
        </div>
      )}

      {/* Input */}
      <div className="rag-input-dock">
        <RagChatInput onSend={sendMessage} isLoading={isLoading || globalUploading} onFileUpload={handleFileUpload} />
      </div>
    </div>
  );
}
