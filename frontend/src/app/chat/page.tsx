'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ChatMessage from '@/components/ChatMessage';
import TypingIndicator from '@/components/TypingIndicator';
import styles from './page.module.css';

interface Session {
  id: number;
  title: string;
  created_at: string;
}

export default function Chat() {
  const [messages, setMessages] = useState<{ role: 'user' | 'ai', content: string }[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const [username, setUsername] = useState('Student');
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);

  // UI States
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [editingSessionId, setEditingSessionId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState('');

  useEffect(() => {
    // Check auth
    const token = localStorage.getItem('token');
    const storedUser = localStorage.getItem('username');
    if (!token) {
      router.push('/login');
      return;
    }
    if (storedUser) setUsername(storedUser);

    // Fetch sessions
    fetchSessions();
  }, [router]);

  const fetchSessions = async () => {
    try {
      const hostname = window.location.hostname;
      const token = localStorage.getItem('token');
      const port = process.env.NODE_ENV === 'production' ? '' : ':8000';
      const response = await fetch(`http://${hostname}${port}/sessions`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setSessions(data);
      }
    } catch (e) {
      console.error('Failed to fetch sessions');
    }
  };

  const loadSession = async (sessionId: number) => {
    setCurrentSessionId(sessionId);
    setIsSidebarOpen(false); // auto-close on mobile/select
    try {
      const hostname = window.location.hostname;
      const token = localStorage.getItem('token');
      const port = process.env.NODE_ENV === 'production' ? '' : ':8000';
      const response = await fetch(`http://${hostname}${port}/sessions/${sessionId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
      }
    } catch (e) {
      console.error('Failed to load session');
    }
  };

  const createNewSession = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setIsSidebarOpen(false);
  };

  const handleDeleteSession = async (sessionId: number, e: React.MouseEvent) => {
    e.stopPropagation(); // prevent loading session
    if (!confirm('Apakah kamu yakin ingin menghapus chat ini?')) return;

    try {
      const hostname = window.location.hostname;
      const token = localStorage.getItem('token');
      const port = process.env.NODE_ENV === 'production' ? '' : ':8000';
      const response = await fetch(`http://${hostname}${port}/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        if (currentSessionId === sessionId) {
          createNewSession();
        }
        fetchSessions();
      }
    } catch (error) {
      console.error('Failed to delete session');
    }
  };

  const handleRenameSession = async (sessionId: number) => {
    if (!editTitle.trim()) {
      setEditingSessionId(null);
      return;
    }

    try {
      const hostname = window.location.hostname;
      const token = localStorage.getItem('token');
      const port = process.env.NODE_ENV === 'production' ? '' : ':8000';
      const response = await fetch(`http://${hostname}${port}/sessions/${sessionId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ title: editTitle.trim() })
      });
      if (response.ok) {
        fetchSessions();
      }
    } catch (error) {
      console.error('Failed to rename session');
    } finally {
      setEditingSessionId(null);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const currentInput = inputRef.current?.value || '';
    if (!currentInput.trim() || isLoading) return;

    const userQuery = currentInput.trim();
    if (inputRef.current) inputRef.current.value = '';
    setMessages(prev => [...prev, { role: 'user', content: userQuery }]);
    setIsLoading(true);

    try {
      const hostname = window.location.hostname;
      const token = localStorage.getItem('token');
      const payload: any = { query: userQuery, chat_history: "" };
      if (currentSessionId) {
        payload.session_id = currentSessionId;
      }

      const port = process.env.NODE_ENV === 'production' ? '' : ':8000';
      const response = await fetch(`http://${hostname}${port}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      setMessages(prev => [...prev, { role: 'ai', content: data.response }]);

      // If it was a new session, update ID and refresh list
      if (!currentSessionId && data.session_id) {
        setCurrentSessionId(data.session_id);
        fetchSessions();
      }

    } catch (error) {
      setMessages(prev => [...prev, { role: 'ai', content: 'Maaf ya, sistem sedang gangguan. Coba lagi sebentar ya!' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignOut = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    router.push('/');
  };

  return (
    <div className={styles.layout}>
      {/* Sidebar Overlay (optional, for mobile) */}

      <aside className={`${styles.sidebar} ${!isSidebarOpen ? styles.sidebarHidden : ''}`}>
        <div className={styles.sidebarHeader}>
          <h3>Riwayat Chat</h3>
          <button className={styles.iconBtn} onClick={() => setIsSidebarOpen(false)}>✕</button>
        </div>
        <div style={{ padding: '12px' }}>
          <button className={styles.newChatBtn} onClick={createNewSession}>
            <span>➕</span> Chat Baru
          </button>
        </div>
        <div className={styles.sessionList}>
          {sessions.map(s => (
            <div
              key={s.id}
              className={styles.sessionItemWrapper}
            >
              {editingSessionId === s.id ? (
                <input
                  type="text"
                  className={styles.editInput}
                  value={editTitle}
                  onChange={e => setEditTitle(e.target.value)}
                  onBlur={() => handleRenameSession(s.id)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') handleRenameSession(s.id);
                    if (e.key === 'Escape') setEditingSessionId(null);
                  }}
                  autoFocus
                />
              ) : (
                <>
                  <button
                    className={`${styles.sessionItem} ${currentSessionId === s.id ? styles.sessionItemActive : ''}`}
                    onClick={() => loadSession(s.id)}
                  >
                    💬 {s.title}
                  </button>
                  <div className={styles.sessionActions}>
                    <button
                      className={styles.actionBtn}
                      onClick={(e) => {
                        e.stopPropagation();
                        setEditTitle(s.title);
                        setEditingSessionId(s.id);
                      }}
                      title="Ubah Nama"
                    >
                      ✏️
                    </button>
                    <button
                      className={styles.actionBtn}
                      onClick={(e) => handleDeleteSession(s.id, e)}
                      title="Hapus"
                    >
                      🗑️
                    </button>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      </aside>

      <div className={styles.container}>
        <header className={styles.header}>
          <div className={styles.leftControls}>
            <button className={styles.iconBtn} onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
              ☰
            </button>
            <div className={styles.userInfo}>
              <span className={styles.username}>Hermeneutic AI</span>
            </div>
          </div>

          <div className={styles.userProfileContainer}>
            <button
              className={styles.userProfileBtn}
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
            >
              🎓
            </button>

            {isUserMenuOpen && (
              <div className={styles.popover}>
                <div className={styles.popoverAvatar}>👤</div>
                <h3 className={styles.popoverName}>{username}</h3>
                <p className={styles.popoverGrade}>Kelas 6</p>
                <button className={styles.popoverSignOut} onClick={handleSignOut}>
                  Keluar 🚪
                </button>
              </div>
            )}
          </div>
        </header>

        <main className={styles.main}>
          <div className={styles.chatContainer}>
            <div className={styles.messageList}>
              {messages.length === 0 && (
                <div style={{ textAlign: 'center', color: '#64748b', marginTop: '40px' }}>
                  <h2>Mulai Percakapan Baru!</h2>
                  <p>Ketikkan pertanyaanmu di bawah ini.</p>
                </div>
              )}
              {messages.map((msg, idx) => (
                <ChatMessage key={idx} role={msg.role} content={msg.content} />
              ))}
              {isLoading && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </div>

            <form className={styles.inputArea} onSubmit={handleSend}>
              <input
                type="text"
                className={styles.inputField}
                placeholder="Ketik pertanyaanmu di sini..."
                ref={inputRef}
                disabled={isLoading}
              />
              <button
                type="submit"
                className={styles.sendButton}
                disabled={isLoading}
              >
                Kirim ✈️
              </button>
            </form>
          </div>
        </main>
      </div>
    </div>
  );
}
