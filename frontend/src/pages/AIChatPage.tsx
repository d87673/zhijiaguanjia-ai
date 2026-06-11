import { useState, useRef, useEffect } from 'react';
import { Button, Card, Input } from '@/components/ui';
import api from '@/lib/api';
import type { ChatResponse } from '@/types';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

const SYSTEM_PROMPT: Message = {
  role: 'system',
  content: '你是一个专业的家政服务AI客服，名为"小智"。请友好热情地接待客户，了解客户需要的服务类型，帮助客户下单预约。回复简洁有力，单次不超过300字。',
};

export function AIChatPage() {
  const [messages, setMessages] = useState<Message[]>([SYSTEM_PROMPT]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async () => {
    if (!input.trim() || sending) return;
    const userMsg: Message = { role: 'user', content: input.trim() };
    setMessages((m) => [...m, userMsg]);
    setInput('');
    setSending(true);

    try {
      const conversation = [...messages, userMsg].filter((m) => m.role !== 'system').map((m) => ({
        role: m.role,
        content: m.content,
      }));
      const { data } = await api.post<ChatResponse>('/ai', {
        action: 'chat',
        messages: [{ role: 'system', content: SYSTEM_PROMPT.content }, ...conversation],
      });
      setMessages((m) => [...m, { role: 'assistant', content: data.reply }]);
    } catch {
      setMessages((m) => [...m, { role: 'assistant', content: '抱歉，AI服务暂时不可用，请稍后重试。' }]);
    } finally {
      setSending(false);
    }
  };

  const displayedMessages = messages.filter((m) => m.role !== 'system');

  return (
    <div className="space-y-4" style={{ height: 'calc(100vh - 120px)' }}>
      <div>
        <h2 className="text-2xl font-bold text-gray-900">AI 客服</h2>
        <p className="text-gray-500 mt-1">智能客服小智为您服务</p>
      </div>

      <Card className="flex-1 flex flex-col overflow-hidden" padding="none">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4" style={{ maxHeight: 'calc(100vh - 320px)' }}>
          {displayedMessages.length === 0 && (
            <div className="text-center text-gray-400 py-12">
              <p className="text-lg">👋 我是小智，您的AI客服助手</p>
              <p className="text-sm mt-2">有什么可以帮您的？</p>
            </div>
          )}
          {displayedMessages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-md'
                    : 'bg-gray-100 text-gray-900 rounded-bl-md'
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
          {sending && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-2.5">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-gray-200 px-4 py-3 flex gap-3">
          <input
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()}
            placeholder="输入您的问题..."
            disabled={sending}
          />
          <Button onClick={send} loading={sending} disabled={!input.trim()}>
            发送
          </Button>
        </div>
      </Card>
    </div>
  );
}
