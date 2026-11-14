import React, { createContext, useContext, useState } from 'react';
import { translations, type Language } from '../i18n';

export type UserMode = 'simple' | 'expert';

interface PreferencesContextType {
  mode: UserMode;
  setMode: (mode: UserMode) => void;
  toggleMode: () => void;
  language: Language;
  setLanguage: (lang: Language) => void;
  toggleLanguage: () => void;
  t: (key: string) => string;
  isHelpOpen: boolean;
  setIsHelpOpen: (open: boolean) => void;
  helpTopic: string | null;
  openHelp: (topic?: string) => void;
  closeHelp: () => void;
}

const PreferencesContext = createContext<PreferencesContextType | undefined>(undefined);

export const PreferencesProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [mode, setModeState] = useState<UserMode>(() => {
    const saved = localStorage.getItem('verisight_mode');
    return saved === 'expert' ? 'expert' : 'simple'; // Default is simple
  });

  const [language, setLanguageState] = useState<Language>(() => {
    const saved = localStorage.getItem('verisight_lang');
    return saved === 'hi' ? 'hi' : 'en'; // Default is English
  });

  const [isHelpOpen, setIsHelpOpen] = useState(false);
  const [helpTopic, setHelpTopic] = useState<string | null>(null);

  const setMode = (newMode: UserMode) => {
    setModeState(newMode);
    localStorage.setItem('verisight_mode', newMode);
  };

  const toggleMode = () => {
    setMode(mode === 'simple' ? 'expert' : 'simple');
  };

  const setLanguage = (newLang: Language) => {
    setLanguageState(newLang);
    localStorage.setItem('verisight_lang', newLang);
  };

  const toggleLanguage = () => {
    setLanguage(language === 'en' ? 'hi' : 'en');
  };

  const openHelp = (topic?: string) => {
    if (topic) setHelpTopic(topic);
    setIsHelpOpen(true);
  };

  const closeHelp = () => {
    setIsHelpOpen(false);
    setHelpTopic(null);
  };

  const t = (key: string): string => {
    const item = translations[key];
    if (!item) return key;
    return item[language] || item.en || key;
  };

  return (
    <PreferencesContext.Provider
      value={{
        mode,
        setMode,
        toggleMode,
        language,
        setLanguage,
        toggleLanguage,
        t,
        isHelpOpen,
        setIsHelpOpen,
        helpTopic,
        openHelp,
        closeHelp,
      }}
    >
      {children}
    </PreferencesContext.Provider>
  );
};

export const usePreferences = (): PreferencesContextType => {
  const context = useContext(PreferencesContext);
  if (!context) {
    throw new Error('usePreferences must be used within a PreferencesProvider');
  }
  return context;
};
