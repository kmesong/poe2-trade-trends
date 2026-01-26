import { useEffect, useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { StatCard } from './components/StatCard';
import type { Data, WeaponData } from './types';

function App() {

  const [data, setData] = useState<Data | null>(null);
  const [activeType, setActiveType] = useState<string>('Bow');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/stats.json')
      .then(res => res.json())
      .then(d => {
        setData(d);
        if (!d['Bow']) {
          const firstKey = Object.keys(d)[0];
          if (firstKey) setActiveType(firstKey);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load data", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-poe-bg text-poe-gold animate-pulse">
        Loading Artifacts...
      </div>
    );
  }

  if (!data) return <div className="text-red-500 p-10">Error loading data.</div>;

  const activeData: WeaponData | undefined = data[activeType];

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


  const handleDataRefresh = (newData: Data) => {
    setData(newData);
    // If the currently active type is not in the new data, switch to the first available one
    if (!newData[activeType]) {
      const firstKey = Object.keys(newData)[0];
      if (firstKey) setActiveType(firstKey);
    }
  };

  return (
    <div className="flex min-h-screen bg-poe-bg text-gray-200 font-sans">
      <Sidebar 
        data={data}
        activeType={activeType} 
        onSelect={setActiveType} 
        onDataRefresh={handleDataRefresh}
      />

      <main className="ml-64 flex-1 p-6 overflow-x-hidden">
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
      </main>
    </div>
  );
}



export default App;
