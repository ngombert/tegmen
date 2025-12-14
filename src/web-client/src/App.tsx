import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatLayout } from './components/ChatLayout';

import { api } from './api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  data?: any;
}

function App() {
  const [currentUser, setCurrentUser] = useState('famille');
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Bonjour ! Je suis Tegmen, votre assistant familial. Qui êtes-vous aujourd\'hui ?' }
  ]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async (text: string) => {
    // Optimistic Update
    const newMessages: Message[] = [...messages, { role: 'user', content: text }];
    setMessages(newMessages);
    setIsLoading(true);

    // Real API call
    try {
      const response = await api.sendMessage(text, currentUser, sessionId);

      // Update session ID if new
      if (response.session_id && response.session_id !== sessionId) {
        setSessionId(response.session_id);
      }

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.message,
        data: response.route !== 'unknown' ? { agent: response.agent, route: response.route } : undefined
      }]);
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "Désolé, une erreur est survenue lors de la communication avec Maestro."
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-white overflow-hidden font-sans text-slate-900 antialiased selection:bg-blue-100 selection:text-blue-900">
      <Sidebar
        currentUser={currentUser}
        onUserSelect={setCurrentUser}
      />
      <main className="flex-1 flex flex-col items-center justify-center bg-slate-50">
        <div className="w-full h-full max-w-5xl bg-white shadow-2xl shadow-slate-200/50 overflow-hidden flex flex-col">
          <ChatLayout
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
