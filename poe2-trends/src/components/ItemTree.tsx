import React, { useState, useEffect, useMemo, useRef } from 'react';
import toast from 'react-hot-toast';

interface CustomCategory {
  id: number;
  name: string;
  items: string[];
}

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
  
  const [customCategories, setCustomCategories] = useState<CustomCategory[]>([]);
  const [isCreatingGroup, setIsCreatingGroup] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');

  useEffect(() => {
    fetchItems();
    fetchCustomCategories();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchCustomCategories = async () => {
    try {
      const response = await fetch('/api/db/custom-categories');
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setCustomCategories(data.data);
        }
      }
    } catch (error) {
      console.error('Failed to fetch custom categories:', error);
    }
  };

  const createCustomGroup = async () => {
    if (!newGroupName.trim()) {
      toast.error('Please enter a group name');
      return;
    }
    
    const selectedNames = new Set<string>();
    selectedItems.forEach(id => {
      const item = items.find(i => i.id === id);
      if (item) selectedNames.add(item.name);
    });

    if (selectedNames.size === 0) {
      toast.error('Select items first to create a group');
      return;
    }

    try {
      const response = await fetch('/api/db/custom-categories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newGroupName,
          items: Array.from(selectedNames)
        })
      });

      if (response.ok) {
        toast.success('Group created!');
        setNewGroupName('');
        setIsCreatingGroup(false);
        fetchCustomCategories();
      } else {
        const data = await response.json();
        toast.error(data.error || 'Failed to create group');
      }
    } catch (e) {
      toast.error('Failed to create group');
    }
  };

  const deleteCustomGroup = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Delete this custom group?')) return;

    try {
      const response = await fetch(`/api/db/custom-categories/${id}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        toast.success('Group deleted');
        fetchCustomCategories();
      } else {
        toast.error('Failed to delete group');
      }
    } catch (e) {
      toast.error('Failed to delete group');
    }
  };

  const toggleCustomGroup = (group: CustomCategory) => {
    const groupItemIds = items
      .filter(item => group.items.includes(item.name))
      .map(item => item.id);
      
    if (groupItemIds.length === 0) return;

    const allSelected = groupItemIds.every(id => selectedItems.has(id));
    const newSelected = new Set(selectedItems);

    if (allSelected) {
      groupItemIds.forEach(id => newSelected.delete(id));
    } else {
      groupItemIds.forEach(id => newSelected.add(id));
    }

    setSelectedItems(newSelected);
    notifySelection(newSelected);
  };

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

  const toggleCategoryAll = (_category: string, categoryItems: ItemEntry[]) => {
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
              Select Items ({selectedItems.size} selected)
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

        <div className="mt-2 pt-2 border-t border-poe-border/30">
          {!isCreatingGroup ? (
            <button
              onClick={() => setIsCreatingGroup(true)}
              className="text-xs text-poe-gold hover:underline flex items-center gap-1"
            >
              <span>+</span> Save Selection as Group
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Group Name"
                value={newGroupName}
                onChange={(e) => setNewGroupName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && createCustomGroup()}
                className="flex-1 bg-black/40 border border-poe-border rounded px-2 py-1 text-xs text-poe-highlight focus:border-poe-gold focus:outline-none"
                autoFocus
              />
              <button
                onClick={createCustomGroup}
                className="text-xs bg-poe-gold/20 hover:bg-poe-gold/40 text-poe-gold px-2 py-1 rounded border border-poe-gold/50"
              >
                Save
              </button>
              <button
                onClick={() => setIsCreatingGroup(false)}
                className="text-xs text-gray-400 hover:text-gray-300"
              >
                ✕
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Tree */}
      <div className="max-h-96 overflow-y-auto">
        {customCategories.length > 0 && !searchTerm && (
          <div className="border-b border-poe-border/30 bg-poe-card/20">
             <div className="px-4 py-2 flex items-center gap-2">
                <span className="text-poe-golddim text-sm font-bold">Custom Groups</span>
             </div>
             <div className="bg-black/10 pb-2">
               {customCategories.map(group => {
                 const groupItemIds = items
                   .filter(item => group.items.includes(item.name))
                   .map(item => item.id);
                 
                 const allSelected = groupItemIds.length > 0 && groupItemIds.every(id => selectedItems.has(id));
                 const someSelected = groupItemIds.some(id => selectedItems.has(id));

                 return (
                   <div 
                     key={group.id} 
                     className="flex items-center gap-2 px-8 py-1.5 hover:bg-white/5 cursor-pointer group relative"
                     onClick={() => toggleCustomGroup(group)}
                   >
                     <IndeterminateCheckbox
                        checked={allSelected}
                        indeterminate={someSelected && !allSelected}
                        readOnly
                        className="accent-poe-gold"
                     />
                     <span className="text-gray-300 text-sm flex-1">{group.name}</span>
                     <span className="text-gray-600 text-xs mr-2">({group.items.length})</span>
                     
                     <button
                       onClick={(e) => deleteCustomGroup(group.id, e)}
                       className="text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity p-1"
                       title="Delete Group"
                     >
                       ✕
                     </button>
                   </div>
                 );
               })}
             </div>
          </div>
        )}

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
