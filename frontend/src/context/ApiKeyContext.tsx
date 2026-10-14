import React, { createContext, useContext, useState, useEffect } from 'react';
import { setSessionGroqApiKey, getSessionGroqApiKey } from '../api/client';

interface ApiKeyContextType {
  apiKey: string;
  hasApiKey: boolean;
  setApiKey: (key: string) => void;
  clearApiKey: () => void;
}

const ApiKeyContext = createContext<ApiKeyContextType | undefined>(undefined);

export const ApiKeyProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Volatile React state: starts empty on initial load/page refresh.
  // Never read from or written to localStorage, sessionStorage, or cookies.
  const [apiKey, setApiKeyState] = useState<string>('');

  const setApiKey = (key: string) => {
    const trimmed = key.trim();
    setApiKeyState(trimmed);
    setSessionGroqApiKey(trimmed);
  };

  const clearApiKey = () => {
    setApiKeyState('');
    setSessionGroqApiKey('');
  };

  useEffect(() => {
    // Ensure synchronization on mount (empty by design on page refresh)
    setSessionGroqApiKey(apiKey);
  }, []);

  return (
    <ApiKeyContext.Provider
      value={{
        apiKey,
        hasApiKey: Boolean(apiKey),
        setApiKey,
        clearApiKey,
      }}
    >
      {children}
    </ApiKeyContext.Provider>
  );
};

export const useApiKey = () => {
  const context = useContext(ApiKeyContext);
  if (!context) {
    throw new Error('useApiKey must be used within an ApiKeyProvider');
  }
  return context;
};
