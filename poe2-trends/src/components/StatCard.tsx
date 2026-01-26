import React from 'react';
import type { Stat } from '../types';

interface Props {
  stat: Stat;
}

export const StatCard: React.FC<Props> = ({ stat }) => {
  let typeColor = 'bg-blue-600';
  let percentageColor = 'text-blue-400';
  let typeLabel = null;
  
  if (stat.type === 'rune') {
      typeColor = 'bg-sky-400';
      percentageColor = 'text-sky-400';
      typeLabel = 'Rune';
  } else if (stat.type === 'bonded') {
      typeColor = 'bg-purple-500'; // Bonded gets Purple
      percentageColor = 'text-purple-400';
      typeLabel = 'Bonded';
  } else if (stat.type === 'implicit') {
      typeColor = 'bg-indigo-600';
      percentageColor = 'text-indigo-400';
      typeLabel = 'Implicit';
  } else if (stat.type === 'prefix') {
      typeColor = 'bg-red-500';
      percentageColor = 'text-red-400';
      typeLabel = 'Prefix';
  } else if (stat.type === 'suffix') {
      typeColor = 'bg-blue-500';
      percentageColor = 'text-blue-400';
      typeLabel = 'Suffix';
  } else if (stat.type === 'fractured') {
      typeColor = 'bg-amber-600';
      percentageColor = 'text-amber-500';
      typeLabel = 'Fractured';
  }


  const formatNameWithValues = () => {
    if (!stat.values || stat.values.length === 0) return stat.name;
    
    const parts = stat.name.split('#');
    if (parts.length <= 1) return stat.name;

    return (
      <span>
        {parts.map((part, i) => {
          const val = stat.values[i];
          if (i === parts.length - 1) return <span key={i}>{part}</span>;
          
          if (!val) return <span key={i}>{part}#</span>;

          return (
            <React.Fragment key={i}>
              <span>{part}</span>
              <span className="inline-flex flex-col align-middle mx-0.5 bg-poe-bg/80 px-1 py-0 rounded border border-poe-border/50 text-[10px]">
                 <span className="text-poe-highlight font-bold leading-none">{val.avg}</span>
                 {val.min !== val.max && (
                   <span className="text-[8px] text-gray-500 leading-none">
                     {val.min}-{val.max}
                   </span>
                 )}
              </span>
            </React.Fragment>
          );
        })}
      </span>
    );
  };

  return (
    <div className="bg-poe-card border border-poe-border p-2 rounded hover:border-poe-golddim transition-colors group flex items-center gap-2">
      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-start mb-1">
          <div className="flex flex-col min-w-0 pr-2">
            <span className="text-gray-200 font-medium text-xs group-hover:text-poe-highlight transition-colors leading-snug">
              {formatNameWithValues()}
            </span>
          </div>
          
          <div className="flex items-center gap-2 shrink-0 self-start">
             {typeLabel && <span className={`text-[10px] ${percentageColor} uppercase tracking-wider font-bold`}>{typeLabel}</span>}
             <span className="text-[10px] text-gray-500">{stat.count}</span>
             <span className={`${percentageColor} font-bold text-xs w-8 text-right`}>
              {stat.percentage}%
            </span>
          </div>
        </div>
        
        <div className="w-full bg-poe-bg rounded-full h-1 overflow-hidden border border-poe-border/50">
          <div 
            className={`h-full ${typeColor} transition-all duration-500 ease-out`}
            style={{ width: `${stat.percentage}%` }}
          />
        </div>
      </div>
    </div>
  );
};

