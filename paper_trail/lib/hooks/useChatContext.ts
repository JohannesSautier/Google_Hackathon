'use client';

import { useState, useEffect } from 'react';

interface MigrationContext {
  fromCountry?: string;
  toCountry?: string;
  visaType?: string;
  currentPhase?: string;
  timeline?: any[];
  documents?: any[];
  [key: string]: any;
}

export function useChatContext() {
  const [context, setContext] = useState<MigrationContext>({});

  useEffect(() => {
    // Try to get context from sessionStorage
    const migrationContext = sessionStorage.getItem('migrationContext');
    const initialQuery = sessionStorage.getItem('initialQuery');
    
    if (migrationContext) {
      try {
        const parsedContext = JSON.parse(migrationContext);
        setContext(parsedContext);
      } catch (error) {
        console.error('Error parsing migration context:', error);
      }
    } else if (initialQuery) {
      // If no structured context, use the initial query as context
      setContext({ initialQuery });
    }

    // Listen for context updates
    const handleStorageChange = () => {
      const updatedContext = sessionStorage.getItem('migrationContext');
      if (updatedContext) {
        try {
          const parsedContext = JSON.parse(updatedContext);
          setContext(parsedContext);
        } catch (error) {
          console.error('Error parsing updated migration context:', error);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);

  const updateContext = (newContext: Partial<MigrationContext>) => {
    const updatedContext = { ...context, ...newContext };
    setContext(updatedContext);
    sessionStorage.setItem('migrationContext', JSON.stringify(updatedContext));
  };

  const clearContext = () => {
    setContext({});
    sessionStorage.removeItem('migrationContext');
    sessionStorage.removeItem('initialQuery');
  };

  return {
    context,
    updateContext,
    clearContext,
  };
}
