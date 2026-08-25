import { useNavigate, useLocation } from 'react-router-dom';

export default function RagFloatingButton() {
  const navigate = useNavigate();
  const location = useLocation();

  // Don't show the button if already on the RAG chat page
  if (location.pathname === '/rag-chat') return null;

  return (
    <button
      className="rag-fab"
      id="rag-fab-btn"
      onClick={() => navigate('/rag-chat')}
      title="Open RAG Assistant"
      aria-label="Open RAG Assistant"
    >
      {/* Chat bot SVG icon */}
      <svg
        className="rag-fab-icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        <circle cx="9" cy="10" r="1" fill="currentColor" stroke="none" />
        <circle cx="15" cy="10" r="1" fill="currentColor" stroke="none" />
      </svg>
      <span className="rag-fab-label">RAG</span>
      <span className="rag-fab-pulse" />
    </button>
  );
}
