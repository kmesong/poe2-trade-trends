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

export interface BatchResult {
  base_type: string;
  normal_avg_chaos: number;
  magic_avg_chaos: number;
  gap_chaos: number;
}
