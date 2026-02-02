import { useEffect, useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { DashboardGrid } from './components/DashboardGrid';
import { Settings } from './pages/Settings';
import { BatchAnalysis } from './pages/BatchAnalysis';
import { Routes, Route } from 'react-router-dom';
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

  const handleDataRefresh = (newData: Data) => {
    setData(newData);
    // If the currently active type is not in the new data, switch to the first available one
    if (!newData[activeType]) {
      const firstKey = Object.keys(newData)[0];
      if (firstKey) setActiveType(firstKey);
    }
  };

  const activeData: WeaponData | undefined = data ? data[activeType] : undefined;

  return (
    <div className="flex min-h-screen bg-poe-bg text-gray-200 font-sans">
      <Sidebar 
        data={data}
        activeType={activeType} 
        onSelect={setActiveType} 
        onDataRefresh={handleDataRefresh}
      />

      <main className="ml-64 flex-1">
        <Routes>
          <Route path="/" element={
            loading ? (
               <div className="h-screen w-full flex items-center justify-center text-poe-gold animate-pulse">
                Loading Artifacts...
              </div>
            ) : data ? (
              <DashboardGrid 
                activeType={activeType} 
                activeData={activeData} 
                search={search} 
                setSearch={setSearch} 
              />
            ) : (
              <div className="text-red-500 p-10">Error loading data.</div>
            )
          } />
          <Route path="/settings" element={<Settings />} />
          <Route path="/batch-analysis" element={<BatchAnalysis />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
