import React from 'react';
import { Link } from 'react-router-dom';

const TabletModifiers: React.FC = () => {
  return (
    <div className="min-h-screen bg-poe-bg text-gray-200 font-sans">
      {/* Header with back navigation */}
      <header className="bg-poe-card border-b border-poe-border p-4">
        <div className="max-w-5xl mx-auto flex items-center gap-4">
          <Link 
            to="/" 
            className="text-poe-gold hover:text-poe-highlight transition-colors flex items-center gap-2"
          >
            <span>←</span>
            <span className="text-sm">Back to Dashboard</span>
          </Link>
          <h1 className="font-serif text-2xl text-poe-gold font-bold tracking-wider ml-4">
            Precursor Tablet Crafting Guide
          </h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto p-6">
        <div className="bg-poe-card border border-poe-border rounded-lg p-6">
          <p className="text-gray-400 mb-6">
            Quick-reference table summarizing crafting strategies. Save this for your second monitor while crafting.
          </p>

          <h2 className="text-xl font-serif text-poe-highlight mb-4 border-b border-poe-border pb-2">
            PoE Precursor Tablet Crafting Cheat Sheet
          </h2>

          {/* Main table */}
          <div className="overflow-x-auto mb-8">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-black/40 text-poe-gold">
                  <th className="border border-poe-border p-3 text-left">Tablet Type</th>
                  <th className="border border-poe-border p-3 text-left">Primary Goal</th>
                  <th className="border border-poe-border p-3 text-left">💎 Top Tier / Must-Have Mods</th>
                  <th className="border border-poe-border p-3 text-left">✅ Good Synergy Mods</th>
                  <th className="border border-poe-border p-3 text-left">❌ Bad / Reroll Mods</th>
                  <th className="border border-poe-border p-3 text-left">Economics</th>
                </tr>
              </thead>
              <tbody>
                {/* ABYSS */}
                <tr className="hover:bg-white/5">
                  <td className="border border-poe-border p-3 font-bold text-purple-400">ABYSS</td>
                  <td className="border border-poe-border p-3 text-poe-highlight font-semibold">Max Rare Monsters</td>
                  <td className="border border-poe-border p-3">
                    <ul className="list-disc list-inside space-y-1 text-yellow-300">
                      <li>% Inc Rare Monsters</li>
                      <li>Additional Rare Monsters</li>
                    </ul>
                  </td>
                  <td className="border border-poe-border p-3">
                    <ul className="list-disc list-inside space-y-1 text-green-400">
                      <li>Increased Difficulty/Reward ("Abyssal Mode")</li>
                      <li>% Item Rarity</li>
                      <li>Additional Trove</li>
                    </ul>
                  </td>
                  <td className="border border-poe-border p-3">
                    <ul className="list-disc list-inside space-y-1 text-red-400">
                      <li>Magic Monsters</li>
                      <li>Increased Gold</li>
                      <li>Experience</li>
                    </ul>
                  </td>
                  <td className="border border-poe-border p-3 text-xs">
                    <div><span className="text-gray-400">Base:</span> ~40 Div</div>
                    <div><span className="text-gray-400">Profit:</span> <span className="text-green-400">High</span></div>
                    <div className="text-gray-500 italic">Most expensive base</div>
                  </td>
                </tr>
                {/* DELIRIUM */}
                <tr className="hover:bg-white/5">
                  <td className="border border-poe-border p-3 font-bold text-gray-300">DELIRIUM</td>
                  <td className="border border-poe-border p-3 text-poe-highlight font-semibold">Rarity & Density</td>
                  <td className="border border-poe-border p-3">
                    <ul className="list-disc list-inside space-y-1 text-yellow-300">
                      <li>% Item Rarity (Crucial)</li>
                      <li>% Pack Size</li>
                    </ul>
                  </td>
                  <td className="border border-poe-border p-3">
                    <ul className="list-disc list-inside space-y-1 text-green-400">
                      <li>Fog Dissipates Slower</li>
                      <li>Monster Effectiveness</li>
                    </ul>
                  </td>
                  <td className="border border-poe-border p-3">
                    <ul className="list-disc list-inside space-y-1 text-red-400">
                      <li>Whitestones</li>
                      <li>Simulacrum Splinters</li>
                      <li>Increased Gold</li>
                    </ul>
                  </td>
                  <td className="border border-poe-border p-3 text-xs">
                    <div><span className="text-gray-400">Base:</span> ~15c</div>
                    <div><span className="text-gray-400">Profit:</span> <span className="text-yellow-400">Medium</span></div>
                    <div className="text-gray-500 italic">Volume crafting</div>
                  </td>
                </tr>
                {/* BREACH */}
                <tr className="hover:bg-white/5">
                  <td className="border border-poe-border p-3 font-bold text-purple-500">BREACH</td>
                  <td className="border border-poe-border p-3 text-poe-highlight font-semibold">Clasped Hands</td>
                  <td className="border border-poe-border p-3">
                    <ul className="list-disc list-inside space-y-1 text-yellow-300">
                      <li>Additional Clasped Hands (The Jackpot)</li>
                    </ul>
                  </td>
                  <td className="border border-poe-border p-3">
                    <ul className="list-disc list-inside space-y-1 text-green-400">
                      <li>Additional Breaches</li>
                      <li>Monster Density</li>
                      <li>% Item Rarity</li>
                    </ul>
                  </td>
                  <td className="border border-poe-border p-3">
                    <ul className="list-disc list-inside space-y-1 text-red-400">
                      <li>Breach Splinters</li>
                      <li>Magic Monsters</li>
                    </ul>
                  </td>
                  <td className="border border-poe-border p-3 text-xs">
                    <div><span className="text-gray-400">Base:</span> ~3c</div>
                    <div><span className="text-gray-400">Profit:</span> <span className="text-green-400">Massive if "Hands" hit</span></div>
                    <div className="text-gray-500 italic">Low risk</div>
                  </td>
                </tr>
                {/* RITUAL */}
                <tr className="hover:bg-white/5 bg-red-950/20">
                  <td className="border border-poe-border p-3 font-bold text-red-500">RITUAL</td>
                  <td className="border border-poe-border p-3 text-gray-500">N/A</td>
                  <td className="border border-poe-border p-3 text-red-500 font-bold">DO NOT CRAFT</td>
                  <td className="border border-poe-border p-3 text-red-500 font-bold">DO NOT CRAFT</td>
                  <td className="border border-poe-border p-3 text-red-500 font-bold">DO NOT CRAFT</td>
                  <td className="border border-poe-border p-3 text-xs">
                    <div className="text-red-400">Currency Sink. Avoid.</div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Workflow Section */}
          <h2 className="text-xl font-serif text-poe-highlight mb-4 border-b border-poe-border pb-2">
            🛠️ Quick Crafting Workflow
          </h2>

          <ol className="list-decimal list-inside space-y-3 text-gray-300">
            <li>
              <span className="font-semibold text-poe-gold">Buy Base:</span>{' '}
              Purchase White (Normal) tablets.
            </li>
            <li>
              <span className="font-semibold text-poe-gold">Magic Phase:</span>{' '}
              Use <span className="text-blue-400">Transmute</span> + <span className="text-blue-400">Alterations</span> until you hit <span className="text-yellow-300 font-semibold">ONE</span> "Top Tier" mod from the table above.
            </li>
            <li>
              <span className="font-semibold text-poe-gold">Rare Phase:</span>
              <ul className="list-disc list-inside ml-6 mt-2 space-y-2 text-gray-400">
                <li>Use a <span className="text-yellow-400">Regal Orb</span>.</li>
                <li>
                  <span className="text-green-400">Scenario A:</span> If you have <span className="font-semibold">2 Good Mods</span> (even if one is low tier), use an <span className="text-yellow-400">Exalted Orb</span> to fish for a 3rd.
                </li>
                <li>
                  <span className="text-red-400">Scenario B:</span> If the item has <span className="font-semibold">2 Bad Lines</span> (or fills up prefixes/suffixes with junk), use a <span className="text-yellow-400">Chaos Orb</span> to reroll entirely.
                </li>
              </ul>
            </li>
            <li>
              <span className="font-semibold text-poe-gold">Stop Condition:</span>{' '}
              Generally, stop at <span className="text-green-400 font-semibold">3 decent lines</span> (e.g., 2 Top Tier + 1 Synergy). You do not need 4 perfect lines to make a profit.
            </li>
            <li>
              <span className="font-semibold text-poe-gold">Validation:</span>{' '}
              Always price check on the trade site using your specific combination of mods before rerolling.
            </li>
          </ol>
        </div>
      </main>
    </div>
  );
};

export default TabletModifiers;
