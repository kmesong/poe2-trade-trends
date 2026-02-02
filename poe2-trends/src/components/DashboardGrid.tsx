import React from 'react';
import { StatCard } from './StatCard';
import type { WeaponData } from '../types';

interface Props {
  activeType: string;
  activeData: WeaponData | undefined;
  search: string;
  setSearch: (s: string) => void;
}

export const DashboardGrid: React.FC<Props> = ({ activeType, activeData, search, setSearch }) => {
  const filteredStats = activeData?.stats.filter(stat => 
    stat.name.toLowerCase().includes(search.toLowerCase())
  ) || [];

  const runes = filteredStats.filter(s => s.type === 'rune');
  const bonded = filteredStats.filter(s => s.type === 'bonded');
  const attributes = filteredStats.filter(s => s.type !== 'rune' && s.type !== 'bonded');

  const showAttributes = attributes.length > 0;
  const showRunes = runes.length > 0;
  const showBonded = bonded.length > 0;

  const visibleColumns = [showAttributes, showRunes, showBonded].filter(Boolean).length;
  
  let gridClass = "grid-cols-1";
  if (visibleColumns === 2) gridClass = "lg:grid-cols-2";
  if (visibleColumns === 3) gridClass = "lg:grid-cols-3";

  return (
    <div className="flex-1 p-6 overflow-x-hidden">
        <header className="mb-6 flex justify-between items-end border-b border-poe-border pb-3">
          <div>
            <h2 className="text-2xl font-serif text-poe-highlight mb-1">{activeType}</h2>
            <p className="text-poe-golddim text-xs">
              Analyzed {activeData?.total_items || 0} Mirrored Items
            </p>
          </div>

          <div className="relative">
            <input 
              type="text" 
              placeholder="Filter mods..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-poe-card border border-poe-border rounded px-3 py-1.5 w-64 text-xs focus:border-poe-gold focus:outline-none transition-colors text-poe-highlight"
            />
            <div className="absolute right-3 top-2 text-gray-500 text-xs">
              🔍
            </div>
          </div>
        </header>

        <div className={`grid ${gridClass} gap-4 items-start`}>
            {/* Column 1: Attributes */}
            {showAttributes && (
                <div className="flex flex-col gap-2">
                    <h3 className="text-sm font-serif text-blue-400 border-b border-blue-900/50 pb-1 mb-1 font-bold tracking-wide">
                        Attributes
                    </h3>
                    <div className="flex flex-col gap-2">
                        {attributes.map((stat, idx) => (
                            <StatCard key={`attr-${idx}`} stat={stat} />
                        ))}
                    </div>
                </div>
            )}

            {/* Column 2: Runes */}
            {showRunes && (
                <div className="flex flex-col gap-2">
                    <h3 className="text-sm font-serif text-sky-400 border-b border-sky-900/50 pb-1 mb-1 font-bold tracking-wide">
                        Runes & Enchants
                    </h3>
                    <div className="flex flex-col gap-2">
                        {runes.map((stat, idx) => (
                            <StatCard key={`rune-${idx}`} stat={stat} />
                        ))}
                    </div>
                </div>
            )}

            {/* Column 3: Bonded */}
            {showBonded && (
                <div className="flex flex-col gap-2">
                    <h3 className="text-sm font-serif text-purple-400 border-b border-purple-900/50 pb-1 mb-1 font-bold tracking-wide">
                        Bonded Stats
                    </h3>
                    <div className="flex flex-col gap-2">
                        {bonded.map((stat, idx) => (
                            <StatCard key={`bonded-${idx}`} stat={stat} />
                        ))}
                    </div>
                </div>
            )}
            
            {visibleColumns === 0 && (
                <div className="col-span-full text-center py-20 text-gray-600 italic text-sm">
                  No stats found matching filters
                </div>
            )}
        </div>
      </div>
  );
};
