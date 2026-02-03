export interface StatValue {
  min: number;
  max: number;
  avg: number;
}

export interface Stat {
  name: string;
  type: string;
  count: number;
  percentage: number;
  values: StatValue[];
}

export interface WeaponData {
  total_items: number;
  stats: Stat[];
}

export interface Data {
  [key: string]: WeaponData;
}

export interface ModifierData {
  name: string;
  tier: string;
  mod_type: string;
  rarity: string;
  item_name: string;
  display_text: string;
  magnitude_min: number | null;
  magnitude_max: number | null;
}

export interface BatchResult {
  base_type: string;
  normal_avg_chaos: number;
  crafting_avg_chaos?: number;
  magic_avg_chaos: number;
  gap_chaos: number;
  search_id?: string;
  magic_search_id?: string;
  normal_modifiers?: ModifierData[];
  magic_modifiers?: ModifierData[];
}

export interface ExcludedModifier {
  id: number;
  mod_name_pattern: string | null;
  mod_tier: string | null;
  mod_type: string | null;
  reason: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AnalysisResultDB {
  id: number;
  base_type: string;
  created_at: string;
  normal_avg_chaos: number;
  magic_avg_chaos: number;
  gap_chaos: number;
  search_id: string | null;
  magic_search_id: string | null;
  modifiers: ModifierDB[];
}

export interface ModifierDB {
  id: number;
  name: string;
  tier: string;
  mod_type: string;
  rarity: string;
  item_name: string | null;
  price_chaos: number | null;
  magnitude_min: number | null;
  magnitude_max: number | null;
  mod_group: string | null;
}
