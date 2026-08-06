import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import { Send, Bot, User, AlertTriangle, Sparkles, RefreshCw } from 'lucide-react';

export const ChatbotPage = () => {
  const { user, authFetch } = useAuth();
  const { addToast } = useToast();
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: `Hello ${user?.name || 'there'}! I am your NeuroCare AI clinical assistant. I can help interpret your wearable vitals, explain recent alerts, review scheduled appointments, or answer general neuro-monitoring questions.\n\nHow can I support your care journey today?`,
      timestamp: new Date()
    }
  ]);
  const [userInput, setUserInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [rateLimitCount, setRateLimitCount] = useState(0);
  const messagesEndRef = useRef(null);

  // Auto-scroll to the latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  const handleSendMessage = async (e) => {
    if (e) e.preventDefault();
    if (!userInput.trim() || isSending) return;

    const userMessageText = userInput.trim();
    setUserInput('');
    setIsSending(true);

    // Append user message
    setMessages(prev => [
      ...prev,
      { sender: 'user', text: userMessageText, timestamp: new Date() }
    ]);

    try {
      const res = await authFetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessageText })
      });

      if (!res.ok) {
        if (res.status === 429) {
          throw new Error('Rate limit exceeded: Max 20 queries per hour.');
        }
        const errMsg = await res.text();
        throw new Error(errMsg || 'Failed to connect to assistant.');
      }

      const data = await res.json();
      setMessages(prev => [
        ...prev,
        { sender: 'bot', text: data.response, timestamp: new Date() }
      ]);
      setRateLimitCount(prev => prev + 1);
    } catch (err) {
      console.error(err);
      addToast(err.message, 'error');
      setMessages(prev => [
        ...prev,
        {
          sender: 'bot',
          text: `⚠️ Error: ${err.message || 'I experienced an issue syncing with the clinical database. Please try again shortly.'}`,
          timestamp: new Date()
        }
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleQuickQuestion = (question) => {
    setUserInput(question);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto text-left font-sans select-none" style={{ fontFamily: "'Inter', sans-serif" }}>
      {/* Header and Badge Widget */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-black text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
            <Bot className="w-6 h-6 text-primary" />
            AI Clinical Assistant
          </h1>
          <p className="text-xs font-semibold text-slate-500 mt-1">
            Empathetic companion helping you translate telemetry readings and schedule details.
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Badge status="normal" className="bg-teal-50 text-teal-700 border-teal-200">
            <Sparkles className="w-3 h-3 mr-1 animate-pulse" />
            Virtual Care Companion
          </Badge>
          <Badge status="neutral">
            Requests: {rateLimitCount}/20 hr
          </Badge>
        </div>
      </div>

      {/* Main Chat Container Card */}
      <Card className="h-[600px] flex flex-col p-0 overflow-hidden bg-slate-50/50 dark:bg-slate-950/20 border border-slate-200/80 dark:border-slate-800">
        <div className="flex flex-col h-full">
          
          {/* Scrollable Message Box */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 max-h-[440px]">
            {messages.map((msg, idx) => {
              const isUser = msg.sender === 'user';
              return (
                <div
                  key={idx}
                  className={`flex items-start gap-3.5 max-w-[85%] ${
                    isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
                  }`}
                >
                  {/* Avatar Icon */}
                  <div
                    className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 border ${
                      isUser
                        ? 'bg-teal-50 border-teal-200 text-teal-600 dark:bg-teal-950/50 dark:border-teal-900/50'
                        : 'bg-blue-50 border-blue-200 text-blue-600 dark:bg-blue-950/50 dark:border-blue-900/50'
                    }`}
                  >
                    {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>

                  {/* Message bubble */}
                  <div className="space-y-1">
                    <div
                      className={`px-4 py-2.5 rounded-2xl text-xs font-semibold leading-relaxed shadow-sm whitespace-pre-line ${
                        isUser
                          ? 'bg-teal-600 text-white rounded-tr-none'
                          : 'bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800/80 text-slate-800 dark:text-slate-200 rounded-tl-none'
                      }`}
                    >
                      {msg.text}
                    </div>
                    <span
                      className={`text-[9px] font-black text-slate-400 block px-1 ${
                        isUser ? 'text-right' : 'text-left'
                      }`}
                    >
                      {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              );
            })}

            {isSending && (
              <div className="flex items-start gap-3.5 mr-auto max-w-[80%]">
                <div className="w-8 h-8 rounded-xl bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-900/50 flex items-center justify-center animate-spin">
                  <RefreshCw className="w-4 h-4 text-blue-600" />
                </div>
                <div className="px-4 py-2.5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800/80 text-slate-400 font-semibold text-xs rounded-tl-none animate-pulse">
                  Querying medical data records...
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick replies suggestions */}
          {messages.length === 1 && (
            <div className="px-6 py-2 flex flex-wrap gap-2 justify-start border-t border-slate-100 dark:border-slate-850 pt-3.5">
              {[
                "What is my next appointment details?",
                "Analyze my latest telemetry alerts",
                "Explain how DS18B20 sensor works",
                "What symptoms suggest a heart emergency?"
              ].map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleQuickQuestion(q)}
                  className="px-3 py-1.5 bg-slate-50 hover:bg-slate-100 dark:bg-slate-900 dark:hover:bg-slate-850 text-slate-600 dark:text-slate-400 rounded-lg text-[10px] font-bold border border-slate-200/60 dark:border-slate-850 cursor-pointer transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          {/* Bottom Area: Disclaimer + Input */}
          <div className="p-4 sm:p-6 bg-white dark:bg-slate-950/45 border-t border-slate-100 dark:border-slate-850 space-y-3 mt-auto">
            
            {/* Persistent Disclaimer Banner */}
            <div className="flex items-center gap-2.5 px-4 py-2 bg-amber-50/50 dark:bg-amber-950/10 border border-amber-200/55 dark:border-amber-900/30 rounded-xl text-[10px] font-semibold text-amber-800 dark:text-amber-400 leading-normal">
              <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
              <span>General questions only — not medical advice. For emergencies, use the Emergency Button or call 112 immediately.</span>
            </div>

            {/* Input Submission Bar */}
            <form onSubmit={handleSendMessage} className="flex gap-2">
              <input
                type="text"
                placeholder="Ask about vitals, alerts, or consultation sessions..."
                value={userInput}
                onChange={e => setUserInput(e.target.value)}
                disabled={isSending}
                className="flex-1 px-4 py-3 border border-slate-200 dark:border-slate-800 rounded-xl bg-slate-50 dark:bg-slate-900 text-xs font-semibold text-slate-850 dark:text-slate-200 outline-none focus:border-blue-500 dark:focus:border-blue-700 transition-colors shadow-sm disabled:cursor-not-allowed"
              />
              <Button
                type="submit"
                disabled={!userInput.trim() || isSending}
                variant="primary"
                className="rounded-xl px-4 py-3 cursor-pointer"
                icon={<Send className="w-4 h-4" />}
              >
                Send
              </Button>
            </form>
          </div>

        </div>
      </Card>
    </div>
  );
};

export default ChatbotPage;
