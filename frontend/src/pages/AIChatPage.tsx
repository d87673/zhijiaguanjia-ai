import { useState, useRef, useEffect, useCallback } from 'react';
import { Button, Card } from '@/components/ui';
import api from '@/lib/api';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

const SYSTEM_PROMPT = `你是一个专业的家政服务AI客服，名为"小智"。你需要：
1. 友好热情地接待客户，使用恰当的敬语
2. 了解客户需要什么类型的家政服务（保洁、维修、搬家、月嫂、育儿、陪护等）
3. 询问服务时间、地址、面积等关键信息
4. 根据客户需求推荐合适的服务套餐
5. 帮助客户下单预约
请用中文回复，语气专业亲切。回复简洁有力，单次不超过300字。`;

export function AIChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const send = useCallback(async () => {
    if (!input.trim() || streaming) return;
    const userMsg: Message = { role: 'user', content: input.trim() };
    setMessages((m) => [...m, userMsg]);
    setInput('');
    setStreaming(true);
    setStreamingContent('');

    const conversation = [...messages, userMsg].map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      await doStreamRequest(conversation);
    } catch {
      setMessages((m) => [...m, { role: 'assistant', content: '抱歉，AI服务暂时不可用，请稍后重试。' }]);
    } finally {
      setStreaming(false);
      setStreamingContent('');
    }
  }, [input, messages, streaming]);

  /** Make a streaming fetch request with automatic 401 token refresh. */
  const doStreamRequest = async (conversation: { role: string; content: string }[]) => {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('No token');

    const doFetch = (t: string) =>
      fetch('/api/v1/ai/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${t}`,
        },
        body: JSON.stringify({
          action: 'chat',
          messages: [{ role: 'system', content: SYSTEM_PROMPT }, ...conversation],
        }),
      });

    let response = await doFetch(token);

    // On 401, try to refresh the token and retry once
    if (response.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) throw new Error('Auth required');
      try {
        const { data: refreshData } = await api.post('/auth/refresh', { refresh_token: refreshToken });
        const newAccess = refreshData.access_token;
        localStorage.setItem('access_token', newAccess);
        response = await doFetch(newAccess);
      } catch {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return;
      }
    }

    if (!response.ok) throw new Error('Stream error');
    await readStream(response);
  };

  /** Read SSE stream events and update messages state. */
  async function readStream(response: Response) {
    const reader = response.body?.getReader();
    if (!reader) throw new Error('No reader');

    const decoder = new TextDecoder();
    let buffer = '';
    let fullContent = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') break;
          try {
            const parsed = JSON.parse(data);
            if (parsed.content) {
              fullContent += parsed.content;
              setStreamingContent(fullContent);
            }
          } catch { /* skip invalid JSON */ }
        }
      }
    }

    setMessages((m) => [...m, { role: 'assistant', content: fullContent }]);
  }

  const displayedMessages = messages;
  const isTyping = streaming && streamingContent === '';

  return (
    <div className="space-y-4 flex flex-col" style={{ height: 'calc(100vh - 120px)' }}>
      <div className="shrink-0">
        <h2 className="text-2xl font-bold text-gray-900">AI 客服</h2>
        <p className="text-gray-500 mt-1">智能客服小智为您服务 · 支持流式实时对话</p>
      </div>

      <Card className="flex-1 flex flex-col overflow-hidden" padding="none">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4" style={{ maxHeight: 'calc(100vh - 320px)' }}>
          {displayedMessages.length === 0 && (
            <div className="text-center text-gray-400 py-16">
              <div className="text-5xl mb-4">🤖</div>
              <p className="text-lg font-medium text-gray-500">我是小智，您的AI客服助手</p>
              <p className="text-sm mt-2 text-gray-400">有什么可以帮助您的？</p>
              <div className="mt-6 grid grid-cols-2 gap-2 max-w-sm mx-auto">
                {['我想预约日常保洁', '你们有哪些服务？', '如何下单预约？', '价格怎么算？'].map((q) => (
                  <button
                    key={q}
                    onClick={() => { setInput(q); inputRef.current?.focus(); }}
                    className="text-xs text-gray-500 bg-gray-50 hover:bg-gray-100 rounded-lg px-3 py-2 transition-colors text-left border border-gray-100"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
          {displayedMessages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className="flex gap-2 max-w-[85%]">
                {msg.role === 'assistant' && (
                  <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs shrink-0 mt-1">
                    🤖
                  </div>
                )}
                <div
                  className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white rounded-br-md'
                      : 'bg-gray-100 text-gray-900 rounded-bl-md'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
                {msg.role === 'user' && (
                  <div className="w-7 h-7 rounded-full bg-gray-400 flex items-center justify-center text-white text-xs shrink-0 mt-1">
                    👤
                  </div>
                )}
              </div>
            </div>
          ))}
          {/* Streaming message bubble */}
          {streamingContent && (
            <div className="flex justify-start">
              <div className="flex gap-2 max-w-[85%]">
                <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs shrink-0 mt-1">🤖</div>
                <div className="bg-gray-100 text-gray-900 rounded-2xl rounded-bl-md px-4 py-2.5 text-sm leading-relaxed">
                  <p className="whitespace-pre-wrap">{streamingContent}<span className="inline-block w-1.5 h-4 bg-blue-600 animate-pulse ml-0.5 align-middle" /></p>
                </div>
              </div>
            </div>
          )}
          {isTyping && (
            <div className="flex justify-start">
              <div className="flex gap-2 max-w-[85%]">
                <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs shrink-0 mt-1">🤖</div>
                <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-2.5">
                  <div className="flex gap-1.5">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-gray-200 px-4 py-3 flex gap-3">
          <input
            ref={inputRef}
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-shadow"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
            placeholder="输入您的问题...（Enter发送）"
            disabled={streaming}
          />
          <Button onClick={send} loading={streaming} disabled={!input.trim()}>
            发送
          </Button>
        </div>
      </Card>
    </div>
  );
}
