"use client";

import React, { createContext, useContext, useEffect, useState } from 'react';
import { dictionary, Locale, DictionaryKey } from '@/lib/dictionary';

type LanguageContextType = {
    locale: Locale;
    setLocale: (locale: Locale) => void;
    t: (key: DictionaryKey) => string;
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
    const [locale, setLocaleState] = useState<Locale>('es');

    useEffect(() => {
        // Load preference from localStorage
        const saved = localStorage.getItem('app-locale') as Locale;
        if (saved && (saved === 'es' || saved === 'en')) {
            setLocaleState(saved);
        }
    }, []);

    const setLocale = (newLocale: Locale) => {
        setLocaleState(newLocale);
        localStorage.setItem('app-locale', newLocale);
    };

    const t = (key: DictionaryKey) => {
        return dictionary[locale][key] || key;
    };

    return (
        <LanguageContext.Provider value={{ locale, setLocale, t }}>
            {children}
        </LanguageContext.Provider>
    );
}

export const useLanguage = () => {
    const context = useContext(LanguageContext);
    if (context === undefined) {
        throw new Error('useLanguage must be used within a LanguageProvider');
    }
    return context;
};
