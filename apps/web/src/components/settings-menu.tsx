"use client";

import { useState, useRef, useEffect } from "react";
import { useTheme } from "@/components/theme-provider";
import { useLanguage } from "@/components/language-provider";
import { Moon, Sun, Languages } from "lucide-react";
import { Button } from "@/components/ui/button";

export function SettingsMenu() {
    const { theme, toggleTheme } = useTheme();
    const { locale, setLocale, t } = useLanguage();
    const [isOpen, setIsOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);

    // Close when clicking outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    return (
        <div className="relative" ref={menuRef}>
            <Button
                variant="ghost"
                size="icon"
                className="h-9 w-9 rounded-full"
                onClick={() => setIsOpen(!isOpen)}
            >
                <Languages className="h-[1.2rem] w-[1.2rem]" />
                <span className="sr-only">Settings</span>
            </Button>

            {isOpen && (
                <div className="absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-popover ring-1 ring-black ring-opacity-5 focus:outline-none z-50 animate-in fade-in zoom-in-95 duration-200 border border-border">
                    <div className="py-1">
                        <div className="px-4 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                            {t('settings_lang')}
                        </div>
                        <button
                            onClick={() => { setLocale('es'); setIsOpen(false); }}
                            className={`block w-full text-left px-4 py-2 text-sm hover:bg-muted transition-colors ${locale === 'es' ? 'bg-muted/50 font-medium' : ''}`}
                        >
                            🇪🇸 Español
                        </button>
                        <button
                            onClick={() => { setLocale('en'); setIsOpen(false); }}
                            className={`block w-full text-left px-4 py-2 text-sm hover:bg-muted transition-colors ${locale === 'en' ? 'bg-muted/50 font-medium' : ''}`}
                        >
                            🇺🇸 English
                        </button>

                        <div className="border-t border-border my-1" />

                        <div className="px-4 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                            Theme
                        </div>
                        <button
                            onClick={() => { toggleTheme(); }}
                            className="flex items-center gap-2 w-full text-left px-4 py-2 text-sm hover:bg-muted transition-colors"
                        >
                            {theme === 'dark' ? (
                                <>
                                    <Sun className="h-4 w-4 text-yellow-500" />
                                    <span>{t('settings_theme_light')}</span>
                                </>
                            ) : (
                                <>
                                    <Moon className="h-4 w-4 text-blue-400" />
                                    <span>{t('settings_theme_dark')}</span>
                                </>
                            )}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
