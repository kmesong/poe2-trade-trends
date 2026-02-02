import React, { useState, useEffect, useMemo, useRef } from 'react';

interface IndeterminateCheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  indeterminate?: boolean;
}

const IndeterminateCheckbox: React.FC<IndeterminateCheckboxProps> = ({ indeterminate, ...props }) => {
  const ref = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.indeterminate = !!indeterminate;
    }
  }, [indeterminate]);

  return <input ref={ref} type="checkbox" {...props} />;
};

interface ItemEntry {
  id: string;
  name: string;
  category: string;
}

interface ItemTreeProps {
  onSelectionChange: (selected: string[]) => void;
}

interface CategoryGroup {
  [category: string]: ItemEntry[];
}

export const ItemTree: React.FC<ItemTreeProps> = ({ onSelectionChange }) => {
  const [items, setItems] = useState<ItemEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchItems();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchItems = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/items');
      if (!response.ok) {
        throw new Error('Failed to fetch items');
      }
      const data = await response.json();
      
      // Transform data into flat array with category info
      // The API returns data in a specific structure, adapt as needed
      const parsedItems = parseItemsData(data);
      setItems(parsedItems);
      
      // Expand first few categories by default
      if (parsedItems.length > 0) {
        const categories = [...new Set(parsedItems.map(item => item.category))];
        const initialExpanded = new Set(categories.slice(0, 3));
        setExpandedCategories(initialExpanded);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const parseItemsData = (data: unknown): ItemEntry[] => {
    const result: ItemEntry[] = [];

    if (data && typeof data === 'object' && 'result' in data) {
      const resultData = (data as { result: unknown[] }).result;

      if (Array.isArray(resultData)) {
        resultData.forEach((categoryData: unknown) => {
          if (categoryData && typeof categoryData === 'object') {
            const cat = categoryData as { label?: string; entries?: unknown[] };
            const categoryName = cat.label || 'Unknown';
            const entries = cat.entries;

            if (Array.isArray(entries)) {
              const seenNames = new Set<string>();
              
              entries.forEach((entry: unknown, index) => {
                if (entry && typeof entry === 'object') {
                  const e = entry as { type?: string };
                  if (e.type && !seenNames.has(e.type)) {
                    seenNames.add(e.type);
                    result.push({
                      id: `${categoryName}-${e.type}-${index}`, // Unique ID for React Key (internal use only)
                      name: e.type, // Real Item Name (what we send to API)
                      category: categoryName
                    });
                  }
                }
              });
            }
          }
        });
      }
    }

    return result;
  };

  const notifySelection = (newSelectedIds: Set<string>) => {
    const selectedNames = new Set<string>();
    
    newSelectedIds.forEach(id => {
      const item = items.find(i => i.id === id);
      if (item) {
        selectedNames.add(item.name);
      }
    });
    
    onSelectionChange(Array.from(selectedNames));
  };

  const categories = useMemo(() => {
    const groups: CategoryGroup = {};
    items.forEach(item => {
      if (!groups[item.category]) {
        groups[item.category] = [];
      }
      groups[item.category].push(item);
    });
    return groups;
  }, [items]);

  const filteredItems = useMemo(() => {
    if (!searchTerm.trim()) {
      return items;
    }
    const term = searchTerm.toLowerCase();
    return items.filter(item => 
      item.name.toLowerCase().includes(term) ||
      item.category.toLowerCase().includes(term)
    );
  }, [items, searchTerm]);

  const filteredCategories = useMemo(() => {
    const groups: CategoryGroup = {};
    filteredItems.forEach(item => {
      if (!groups[item.category]) {
        groups[item.category] = [];
      }
      groups[item.category].push(item);
    });
    return groups;
  }, [filteredItems]);

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const toggleItem = (itemId: string) => {
    const newSelected = new Set(selectedItems);
    if (newSelected.has(itemId)) {
      newSelected.delete(itemId);
    } else {
      newSelected.add(itemId);
    }
    setSelectedItems(newSelected);
    notifySelection(newSelected);
  };

  const toggleCategoryAll = (category: string, categoryItems: ItemEntry[]) => {
    const allSelected = categoryItems.every(item => selectedItems.has(item.id));
    const newSelected = new Set(selectedItems);
    
    if (allSelected) {
      // Deselect all in category
      categoryItems.forEach(item => newSelected.delete(item.id));
    } else {
      // Select all in category
      categoryItems.forEach(item => newSelected.add(item.id));
    }
    
    setSelectedItems(newSelected);
    notifySelection(newSelected);
  };

  const selectAll = () => {
    const allIds = filteredItems.map(item => item.id);
    const newSelected = new Set(allIds);
    setSelectedItems(newSelected);
    notifySelection(newSelected);
  };

  const deselectAll = () => {
    setSelectedItems(new Set());
    onSelectionChange([]);
  };

  const categoryCount = Object.keys(categories).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-poe-gold animate-pulse">Loading items...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-900/20 border border-red-500/50 rounded text-red-400">
        Error: {error}
        <button 
          onClick={fetchItems}
          className="ml-4 text-poe-gold hover:underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="bg-poe-card border border-poe-border rounded-lg overflow-hidden">
      {/* Header */}
      <div className="p-4 bg-black/40 border-b border-poe-border">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-poe-highlight font-bold">
            Select Items ({selectedItems.length} selected)
          </h3>
          <div className="flex gap-2">
            <button
              onClick={selectAll}
              className="text-xs text-poe-gold hover:underline"
            >
              Select All
            </button>
            <span className="text-gray-600">|</span>
            <button
              onClick={deselectAll}
              className="text-xs text-gray-400 hover:underline"
            >
              Clear
            </button>
          </div>
        </div>
        
        {/* Search */}
        <input
          type="text"
          placeholder="Search items..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full bg-black/40 border border-poe-border rounded p-2 text-sm text-poe-highlight focus:border-poe-gold focus:outline-none"
        />
      </div>

      {/* Tree */}
      <div className="max-h-96 overflow-y-auto">
        {Object.entries(filteredCategories).map(([category, categoryItems]) => {
          const allSelected = categoryItems.length > 0 && categoryItems.every(item => selectedItems.has(item.id));
          const someSelected = categoryItems.some(item => selectedItems.has(item.id));
          const isExpanded = expandedCategories.has(category);

          return (
            <div key={category} className="border-b border-poe-border/30">
              {/* Category Header */}
              <button
                onClick={() => toggleCategory(category)}
                className="w-full px-4 py-2 flex items-center gap-2 hover:bg-white/5 transition-colors bg-black/20"
              >
                <span className="text-poe-golddim text-sm">
                  {isExpanded ? '▼' : '▶'}
                </span>
                <IndeterminateCheckbox
                  checked={allSelected}
                  indeterminate={someSelected && !allSelected}
                  onChange={() => toggleCategoryAll(category, categoryItems)}
                  onClick={(e: React.MouseEvent) => e.stopPropagation()}
                  className="accent-poe-gold"
                />
                <span className="text-poe-highlight font-medium flex-1 text-left">
                  {category}
                </span>
                <span className="text-gray-500 text-xs">
                  {categoryItems.length} items
                </span>
              </button>

              {/* Items */}
              {isExpanded && (
                <div className="bg-black/10">
                  {categoryItems.map(item => (
                    <label
                      key={item.id}
                      className="flex items-center gap-2 px-8 py-1.5 hover:bg-white/5 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={selectedItems.has(item.id)}
                        onChange={() => toggleItem(item.id)}
                        className="accent-poe-gold"
                      />
                      <span className="text-gray-300 text-sm">
                        {item.name}
                      </span>
                    </label>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="p-3 bg-black/40 border-t border-poe-border text-xs text-gray-500">
        {categoryCount} categories • {items.length} total items
        {searchTerm && (
          <span className="ml-2 text-poe-gold">
            ({filteredItems.length} matching)
          </span>
        )}
      </div>
    </div>
  );
};
