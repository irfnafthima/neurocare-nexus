import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, Paperclip, AlertTriangle, ShieldAlert, Check, CheckCheck, 
  FileText, Image as ImageIcon, Video, Download, User, Info, Lock
} from 'lucide-react';

export const CareTeamChat = ({ user, authFetch, getApiUrl, addToast }) => {
  const [conversations, setConversations] = useState([]);
  const [activeConv, setActiveConv] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [priority, setPriority] = useState('NORMAL'); // 'NORMAL' | 'URGENT' | 'EMERGENCY'
  const [attachmentFile, setAttachmentFile] = useState(null);
  const [attachmentPreview, setAttachmentPreview] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [typingUsers, setTypingUsers] = useState({});
  const [onlineUsers, setOnlineUsers] = useState({});
  const [wsConnected, setWsConnected] = useState(false);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const wsRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, typingUsers]);

  // 1. Fetch Authorized Conversations
  const fetchConversations = async () => {
    if (!user?.token) return;
    try {
      const res = await authFetch(getApiUrl('/chat/conversations'));
      if (res.ok) {
        const data = await res.json();
        setConversations(data);
        if (data.length > 0 && !activeConv) {
          setActiveConv(data[0]);
        }
      }
    } catch (e) {
      console.error('Error fetching chat conversations:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, [user?.token]);

  // 2. Fetch Messages for Active Conversation
  const fetchMessages = async (convId) => {
    if (!convId || !user?.token) return;
    try {
      const res = await authFetch(getApiUrl(`/chat/conversations/${convId}/messages`));
      if (res.ok) {
        const data = await res.json();
        setMessages(data);
      } else if (res.status === 403) {
        addToast('Access denied: You are not authorized for this patient conversation.', 'error');
        setMessages([]);
      }
    } catch (e) {
      console.error('Error fetching messages:', e);
    }
  };

  useEffect(() => {
    if (activeConv?.id) {
      fetchMessages(activeConv.id);
    }
  }, [activeConv?.id]);

  // 3. Setup WebSocket Connection for Active Conversation
  useEffect(() => {
    if (!activeConv?.id || !user?.token) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/chat/${activeConv.id}/?token=${user.token}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onmessage = (e) => {
        try {
          const payload = JSON.parse(e.data);
          if (payload.type === 'chat_message' && payload.message) {
            setMessages((prev) => {
              if (prev.some((m) => m.id === payload.message.id)) return prev;
              return [...prev, payload.message];
            });
            // Update last message in conversation list
            setConversations((prev) =>
              prev.map((c) =>
                c.id === activeConv.id ? { ...c, last_message: payload.message } : c
              )
            );
          } else if (payload.type === 'typing_indicator') {
            if (payload.user_id !== user.id) {
              setTypingUsers((prev) => ({
                ...prev,
                [payload.user_id]: payload.is_typing ? payload.user_name : null,
              }));
            }
          } else if (payload.type === 'user_presence') {
            setOnlineUsers((prev) => ({
              ...prev,
              [payload.user_id]: payload.status === 'ONLINE',
            }));
          }
        } catch (err) {
          console.error('WebSocket parse error:', err);
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
      };

      return () => {
        ws.close();
      };
    } catch (e) {
      console.error('WebSocket init error:', e);
    }
  }, [activeConv?.id, user?.token]);

  // Active polling fallback (every 4s)
  useEffect(() => {
    if (!activeConv?.id) return;
    const interval = setInterval(() => {
      fetchMessages(activeConv.id);
    }, 4000);
    return () => clearInterval(interval);
  }, [activeConv?.id]);

  // Handle typing status broadcast
  const handleTyping = (text) => {
    setInputText(text);
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    wsRef.current.send(
      JSON.stringify({
        type: 'typing',
        is_typing: text.length > 0,
      })
    );

    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    typingTimeoutRef.current = setTimeout(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            type: 'typing',
            is_typing: false,
          })
        );
      }
    }, 2000);
  };

  // Handle Attachment File Selection & Validation
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 25 * 1024 * 1024) {
      addToast('Attachment file exceeds 25MB maximum limit.', 'error');
      return;
    }

    const ext = file.name.split('.').pop().toLowerCase();
    const prohibited = ['exe', 'bat', 'cmd', 'sh', 'php', 'py', 'js', 'dll'];
    if (prohibited.includes(ext)) {
      addToast('Executable file formats are prohibited for clinical security.', 'error');
      return;
    }

    setAttachmentFile(file);
    if (file.type.startsWith('image/')) {
      setAttachmentPreview(URL.createObjectURL(file));
    } else {
      setAttachmentPreview(null);
    }
  };

  // Handle Send Message
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if ((!inputText.trim() && !attachmentFile) || isSending || !activeConv?.id) return;

    try {
      setIsSending(true);
      const formData = new FormData();
      if (inputText.trim()) formData.append('content', inputText.trim());
      formData.append('priority', priority);
      if (attachmentFile) formData.append('attachment', attachmentFile);

      const res = await authFetch(getApiUrl(`/chat/conversations/${activeConv.id}/messages`), {
        method: 'POST',
        body: formData,
      });

      if (res.ok) {
        const newMsg = await res.json();
        setMessages((prev) => [...prev, newMsg]);
        setInputText('');
        setAttachmentFile(null);
        setAttachmentPreview(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
        if (priority === 'EMERGENCY') {
          addToast('Emergency message dispatched to care team.', 'warning');
        }
        setPriority('NORMAL');
      } else if (res.status === 403) {
        addToast('Unauthorized: Your care-team relationship is not active or has been revoked.', 'error');
      } else {
        const errText = await res.text();
        addToast(errText || 'Failed to send message.', 'error');
      }
    } catch (err) {
      console.error('Send message error:', err);
      addToast('Error sending message.', 'error');
    } finally {
      setIsSending(false);
    }
  };

  // Secure attachment download
  const handleDownloadAttachment = async (msg) => {
    try {
      const res = await authFetch(getApiUrl(msg.attachment_url));
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = msg.attachment_original_name || 'attachment';
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      } else if (res.status === 403) {
        addToast('Unauthorized: Permission denied to access this protected clinical attachment.', 'error');
      } else {
        addToast('Failed to download attachment file.', 'error');
      }
    } catch (e) {
      console.error('Attachment download error:', e);
      addToast('Error fetching protected attachment.', 'error');
    }
  };

  const activeTypingText = Object.values(typingUsers).filter(Boolean).join(', ');

  return (
    <div className="flex flex-col h-[calc(100vh-120px)] bg-slate-50 dark:bg-slate-950 rounded-2xl border border-slate-200 dark:border-slate-850 overflow-hidden shadow-sm text-left">
      
      {/* Top Clinical Safety Disclaimer Banner */}
      <div className="bg-amber-50 dark:bg-amber-950/60 border-b border-amber-200 dark:border-amber-900/50 px-4 py-2 flex items-center justify-between gap-3 shrink-0">
        <div className="flex items-center gap-2 text-xs font-semibold text-amber-900 dark:text-amber-300">
          <ShieldAlert className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
          <span>
            <strong>Clinical Notice:</strong> Care-team chat is not an immediate emergency dispatch service. For acute medical emergencies, use the IoT Emergency Button or call local emergency services.
          </span>
        </div>
        <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/60 px-2 py-0.5 rounded shrink-0">
          HIPAA Protected
        </span>
      </div>

      {/* Main Workspace Layout: Conversations Sidebar + Chat Area */}
      <div className="flex flex-1 overflow-hidden">
        
        {/* Left Sidebar: Conversations List */}
        <div className="w-72 sm:w-80 border-r border-slate-200 dark:border-slate-850 bg-white dark:bg-slate-900 flex flex-col shrink-0">
          <div className="p-3.5 border-b border-slate-100 dark:border-slate-850 flex justify-between items-center">
            <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider">
              Care-Team Channels ({conversations.length})
            </span>
            <Lock className="w-3.5 h-3.5 text-slate-400" />
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-850">
            {isLoading ? (
              <div className="p-6 text-center text-xs font-medium text-slate-400">Loading channels...</div>
            ) : conversations.length === 0 ? (
              <div className="p-6 text-center text-xs font-semibold text-slate-400">
                No active care-team channels available.
              </div>
            ) : (
              conversations.map((conv) => {
                const isSelected = activeConv?.id === conv.id;
                return (
                  <div
                    key={conv.id}
                    onClick={() => setActiveConv(conv)}
                    className={`p-3.5 transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-blue-50 dark:bg-blue-950/40 border-l-4 border-blue-600'
                        : 'hover:bg-slate-50 dark:hover:bg-slate-850/50'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-bold text-xs text-slate-900 dark:text-slate-100">
                        Patient {conv.patient_name || conv.patient}
                      </span>
                      {conv.unread_count > 0 && (
                        <span className="px-1.5 py-0.5 rounded-full text-[9px] font-black bg-blue-600 text-white">
                          {conv.unread_count}
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                      {conv.last_message ? conv.last_message.content || 'Attachment sent' : 'No messages yet'}
                    </p>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Main Chat Feed & Composer */}
        <div className="flex-1 flex flex-col bg-slate-50/50 dark:bg-slate-950/50 overflow-hidden">
          {activeConv ? (
            <>
              {/* Chat Header */}
              <div className="px-5 py-3.5 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-850 flex justify-between items-center shrink-0">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-blue-100 dark:bg-blue-900/60 flex items-center justify-center font-black text-xs text-blue-700 dark:text-blue-300">
                    {activeConv.patient_name ? activeConv.patient_name[0] : 'P'}
                  </div>
                  <div>
                    <h4 className="text-xs font-black text-slate-900 dark:text-slate-100">
                      Patient {activeConv.patient_name || activeConv.patient} — Care Team
                    </h4>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-emerald-500' : 'bg-slate-400'}`} />
                      <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase">
                        {wsConnected ? 'Live Channel Connected' : 'Persisted Sync Mode'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-md">
                    Encrypted Care-Team Stream
                  </span>
                </div>
              </div>

              {/* Message Feed Scroll View */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
                {messages.length === 0 ? (
                  <div className="p-8 text-center text-xs text-slate-400 font-medium">
                    No messages recorded in this conversation yet. Send a message to start communicating with the patient care team.
                  </div>
                ) : (
                  messages.map((msg) => {
                    const isSelf = msg.sender === user?.id;
                    return (
                      <div
                        key={msg.id}
                        className={`flex flex-col ${isSelf ? 'items-end' : 'items-start'}`}
                      >
                        <div className="flex items-center gap-1.5 mb-1 text-[10px]">
                          <span className="font-bold text-slate-700 dark:text-slate-300">
                            {isSelf ? 'You' : msg.sender_name}
                          </span>
                          <span className="px-1.5 py-0.2 bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded text-[9px] font-black uppercase">
                            {msg.sender_role}
                          </span>
                          {msg.priority === 'URGENT' && (
                            <span className="bg-amber-100 text-amber-800 text-[9px] font-black px-1.5 py-0.2 rounded border border-amber-300">
                              ⚠️ URGENT
                            </span>
                          )}
                          {msg.is_emergency && (
                            <span className="bg-red-100 text-red-700 text-[9px] font-black px-1.5 py-0.2 rounded border border-red-300 animate-pulse">
                              🚨 EMERGENCY
                            </span>
                          )}
                        </div>

                        <div
                          className={`max-w-md rounded-2xl p-3 text-xs shadow-sm text-left ${
                            isSelf
                              ? 'bg-blue-600 text-white rounded-tr-none'
                              : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 rounded-tl-none'
                          }`}
                        >
                          {msg.content && <p className="leading-relaxed font-medium whitespace-pre-wrap">{msg.content}</p>}

                          {/* Protected Attachment Display */}
                          {msg.has_attachment && (
                            <div className="mt-2 pt-2 border-t border-slate-200/40 dark:border-slate-800">
                              {msg.message_type === 'IMAGE' && (
                                <div className="space-y-1.5">
                                  <img
                                    src={getApiUrl(msg.attachment_url)}
                                    alt="Clinical attachment"
                                    className="max-h-48 rounded-xl object-cover border border-slate-200 dark:border-slate-700 cursor-pointer"
                                    onClick={() => handleDownloadAttachment(msg)}
                                  />
                                </div>
                              )}
                              <button
                                onClick={() => handleDownloadAttachment(msg)}
                                className={`flex items-center gap-2 text-[11px] font-bold mt-1 px-2.5 py-1.5 rounded-lg border cursor-pointer ${
                                  isSelf
                                    ? 'bg-blue-700 text-white border-blue-500 hover:bg-blue-800'
                                    : 'bg-slate-100 dark:bg-slate-800 text-blue-600 dark:text-blue-400 border-slate-200 dark:border-slate-700'
                                }`}
                              >
                                {msg.message_type === 'IMAGE' ? <ImageIcon className="w-3.5 h-3.5" /> : msg.message_type === 'VIDEO' ? <Video className="w-3.5 h-3.5" /> : <FileText className="w-3.5 h-3.5" />}
                                <span>{msg.attachment_original_name || 'Download Attachment'}</span>
                                <Download className="w-3.5 h-3.5 ml-auto" />
                              </button>
                            </div>
                          )}
                        </div>

                        <div className="flex items-center gap-1 mt-1 text-[9px] text-slate-400 font-semibold">
                          <span>{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                          {isSelf && (
                            msg.read_at ? (
                              <CheckCheck className="w-3 h-3 text-blue-500" />
                            ) : (
                              <Check className="w-3 h-3 text-slate-400" />
                            )
                          )}
                        </div>
                      </div>
                    );
                  })
                )}

                {/* Real-Time Typing Indicator */}
                {activeTypingText && (
                  <div className="text-[11px] font-semibold text-blue-600 dark:text-blue-400 italic animate-pulse">
                    {activeTypingText} is typing...
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Message Composer Area */}
              <div className="p-3.5 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-850 shrink-0">
                {/* Priority Selector & Attachment Preview */}
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-slate-400 uppercase">Priority:</span>
                    {['NORMAL', 'URGENT', 'EMERGENCY'].map((p) => (
                      <button
                        key={p}
                        type="button"
                        onClick={() => setPriority(p)}
                        className={`px-2 py-0.5 rounded text-[10px] font-black uppercase cursor-pointer border-none ${
                          priority === p
                            ? p === 'EMERGENCY'
                              ? 'bg-red-600 text-white'
                              : p === 'URGENT'
                              ? 'bg-amber-500 text-white'
                              : 'bg-blue-600 text-white'
                            : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200'
                        }`}
                      >
                        {p === 'EMERGENCY' ? '🚨 Emergency' : p === 'URGENT' ? '⚠️ Urgent' : 'Normal'}
                      </button>
                    ))}
                  </div>

                  {attachmentFile && (
                    <div className="flex items-center gap-1.5 text-xs text-blue-600 dark:text-blue-400 font-bold bg-blue-50 dark:bg-blue-950 px-2 py-0.5 rounded border border-blue-200">
                      <FileText className="w-3.5 h-3.5" />
                      <span className="max-w-[120px] truncate">{attachmentFile.name}</span>
                      <button
                        onClick={() => { setAttachmentFile(null); setAttachmentPreview(null); }}
                        className="text-red-500 hover:text-red-700 border-none bg-transparent font-bold cursor-pointer"
                      >
                        ×
                      </button>
                    </div>
                  )}
                </div>

                <form onSubmit={handleSendMessage} className="flex items-center gap-2">
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    className="hidden"
                    accept="image/*,.pdf,.doc,.docx,.txt,.mp4,.mov,.avi"
                  />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="p-2.5 rounded-xl text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 border-none bg-transparent cursor-pointer"
                    title="Attach Clinical Document or Media"
                  >
                    <Paperclip className="w-5 h-5" />
                  </button>

                  <input
                    type="text"
                    value={inputText}
                    onChange={(e) => handleTyping(e.target.value)}
                    placeholder="Type secure clinical message..."
                    className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs font-medium text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />

                  <button
                    type="submit"
                    disabled={isSending || (!inputText.trim() && !attachmentFile)}
                    className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-xs flex items-center gap-1.5 disabled:opacity-50 border-none cursor-pointer"
                  >
                    <span>Send</span>
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </form>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center p-8 text-center text-xs text-slate-400">
              Select a care-team channel to begin secure clinical communication.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CareTeamChat;
