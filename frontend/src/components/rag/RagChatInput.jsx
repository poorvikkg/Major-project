import { useState, useRef } from 'react';

export default function RagChatInput({ onSend, isLoading, onFileUpload }) {
  const [input, setInput] = useState('');
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  const handleInput = (e) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    if ((input.trim() || file) && !isLoading && !isUploading) {
      onSend(input);
      setInput('');
      if (textareaRef.current) textareaRef.current.style.height = 'auto';
    }
  };

  const handleFileChange = async (e) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setIsUploading(true);
    try {
      await onFileUpload(selectedFile);
    } catch (err) {
      console.error(err);
      alert('Failed to upload document');
      setFile(null);
    } finally {
      setIsUploading(false);
    }
  };

  const removeFile = () => setFile(null);

  return (
    <div className="rag-input-wrapper" id="rag-chat-input">
      {/* File chip */}
      {file && (
        <div className="rag-file-chip">
          {/* Paperclip icon */}
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
          </svg>
          <span className="rag-file-name">{file.name}</span>
          {isUploading ? (
            <span className="rag-file-uploading">Uploading…</span>
          ) : (
            <button onClick={removeFile} className="rag-file-remove" aria-label="Remove file">✕</button>
          )}
        </div>
      )}

      <div className="rag-input-bar">
        {/* Upload button */}
        <button
          className="rag-input-action"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading || isUploading}
          title="Upload Document"
          aria-label="Upload Document"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
          </svg>
          <input
            type="file"
            ref={fileInputRef}
            className="rag-hidden-input"
            accept=".pdf,.csv,.xlsx"
            onChange={handleFileChange}
          />
        </button>

        {/* Text area */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="Ask about police cases, FIRs or crime statistics…"
          className="rag-textarea"
          rows={1}
          disabled={isLoading}
        />

        {/* Send button */}
        <button
          className="rag-send-btn"
          onClick={handleSend}
          disabled={(!input.trim() && !file) || isLoading || isUploading}
          title="Send message"
          aria-label="Send message"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="19" x2="12" y2="5" />
            <polyline points="5 12 12 5 19 12" />
          </svg>
        </button>
      </div>

      <p className="rag-input-disclaimer">
        AI Investigation Assistant can make mistakes. Consider verifying important information.
      </p>
    </div>
  );
}
