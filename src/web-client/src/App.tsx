import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatLayout } from './components/ChatLayout';

import { api } from './api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  data?: any;
}

function App() {
  const [currentUser, setCurrentUser] = useState('user-parent-1');
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Bonjour ! Je suis Tegmen Maestro, votre assistant familial. Sélectionnez un profil pour commencer.' }
  ]);
  const [isLoading, setIsLoading] = useState(false);

  // Synchronize token on user change
  useEffect(() => {
    const syncToken = async () => {
        try {
            await api.getDevToken(currentUser);
            console.log(`Token sync for ${currentUser} successful`);
        } catch (error) {
            console.error("Failed to sync dev token", error);
        }
    };
    syncToken();
  }, [currentUser]);

  const handleSendMessage = async (text: string) => {
    // Optimistic Update
    const newMessages: Message[] = [...messages, { role: 'user', content: text }];
    setMessages(newMessages);
    setIsLoading(true);

    // Real API call
    try {
      const response = await api.sendMessage(text, sessionId);

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.message,
        data: { 
            agent: response.agent, 
            route: response.route,
            ...(response._debug || {})
        }
      }]);
    } catch (error: any) {
      console.error(error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Erreur : ${error.message || "Communication avec Maestro impossible."}`
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
