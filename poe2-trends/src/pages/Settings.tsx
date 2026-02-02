import React, { useEffect, useState } from 'react';
import { getSessionId, saveSessionId } from '../utils/storage';

export const Settings: React.FC = () => {
  const [sessionId, setSessionId] = useState('');
  const [isVisible, setIsVisible] = useState(false);
  const [status, setStatus] = useState<'idle' | 'saved' | 'cleared'>('idle');

  useEffect(() => {
    const stored = getSessionId();
    if (stored) setSessionId(stored);
  }, []);

  const handleSave = () => {
    saveSessionId(sessionId.trim());
    setStatus('saved');
    setTimeout(() => setStatus('idle'), 2000);
  };

  const handleClear = () => {
    setSessionId('');
    saveSessionId('');
    setStatus('cleared');
    setTimeout(() => setStatus('idle'), 2000);
  };

  return (
    <div className="p-8 max-w-4xl mx-auto text-gray-200">
      <h1 className="text-3xl font-serif text-poe-gold mb-8 border-b border-poe-border pb-4">
        Settings
      </h1>

      <div className="bg-poe-card border border-poe-border p-6 rounded-lg shadow-lg">
        <h2 className="text-xl font-bold text-poe-highlight mb-4">API Configuration</h2>
        
        <div className="mb-6">
          <label className="block text-sm font-bold text-poe-golddim mb-2 uppercase tracking-wide">
            POESESSID
          </label>
          <p className="text-xs text-gray-500 mb-3">
            Required for batch analysis to fetch trade data. 
            Found in your browser cookies on pathofexile.com.
          </p>
          
          <div className="relative">
            <input
              type={isVisible ? "text" : "password"}
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
              placeholder="Enter your POESESSID..."
              className="w-full bg-black/40 border border-poe-border rounded p-3 text-sm text-poe-highlight focus:border-poe-gold focus:outline-none transition-colors pr-10"
            />
            <button
              onClick={() => setIsVisible(!isVisible)}
              className="absolute right-3 top-3 text-gray-500 hover:text-gray-300"
            >
              {isVisible ? '🙈' : '👁️'}
            </button>
          </div>
        </div>

        <div className="flex gap-4 items-center">
          <button
            onClick={handleSave}
            className="bg-poe-gold/20 text-poe-gold border border-poe-gold/50 px-6 py-2 rounded hover:bg-poe-gold hover:text-black font-bold transition-all uppercase text-sm tracking-wide"
          >
            Save Configuration
          </button>
          
          <button
            onClick={handleClear}
            className="text-gray-500 hover:text-red-400 text-sm underline transition-colors"
          >
            Clear Session
          </button>

          {status === 'saved' && (
            <span className="text-green-500 text-sm animate-pulse ml-auto">
              ✓ Settings saved successfully
            </span>
          )}
          {status === 'cleared' && (
            <span className="text-yellow-500 text-sm animate-pulse ml-auto">
              ✓ Session cleared
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
