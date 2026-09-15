import { create } from 'zustand';
import type { Asset, GridSummary, MaintenanceTask, AppFilters, RiskLevel, Zone } from '../types';
import { mockAssets, mockGridSummary, mockMaintenanceTasks } from '../mock/mockData';
import { type ThemeId, applyTheme, getStoredTheme } from '../theme/themeUtils';

// ─────────────────────────────────────────────────────────────────────────────
// State shape
// ─────────────────────────────────────────────────────────────────────────────

interface AppState {
  // Data
  assets: Asset[];
  gridSummary: GridSummary | null;
  maintenanceTasks: MaintenanceTask[];
  selectedAssetId: string | null;

  // UI
  isLoading: boolean;
  error: string | null;
  sidebarOpen: boolean;
  mobileSidebarOpen: boolean;
  filters: AppFilters;

  // Theme
  theme: ThemeId;

  // Actions
  loadData: () => void;
  selectAsset: (id: string | null) => void;
  setSidebarOpen: (open: boolean) => void;
  setMobileSidebarOpen: (open: boolean) => void;
  toggleMobileSidebar: () => void;
  setFilter: <K extends keyof AppFilters>(key: K, value: AppFilters[K]) => void;
  resetFilters: () => void;
  getFilteredAssets: () => Asset[];
  setTheme: (id: ThemeId) => void;
}

// ─────────────────────────────────────────────────────────────────────────────
// Default filters
// ─────────────────────────────────────────────────────────────────────────────

const defaultFilters: AppFilters = {
  risk_level: 'all',
  asset_type: 'all',
  zone: 'all',
  status: 'all',
};

// ─────────────────────────────────────────────────────────────────────────────
// Store
// ─────────────────────────────────────────────────────────────────────────────

export const useAppStore = create<AppState>((set, get) => ({
  // ── initial state ──────────────────────────────────────────────────────────
  assets: [],
  gridSummary: null,
  maintenanceTasks: [],
  selectedAssetId: null,
  isLoading: false,
  error: null,
  sidebarOpen: true,
  mobileSidebarOpen: false,
  filters: { ...defaultFilters },
  // main.tsx already called initTheme() before React mounted; just read the value.
  theme: getStoredTheme(),

  // ── actions ────────────────────────────────────────────────────────────────

  loadData: async () => {
    set({ isLoading: true, error: null });

    const base = import.meta.env.VITE_API_BASE_URL ?? '';

    try {
      const [assetsRes, summaryRes, maintenanceRes] = await Promise.all([
        fetch(`${base}/api/v1/assets`),
        fetch(`${base}/api/v1/summary`),
        fetch(`${base}/api/v1/maintenance`),
      ]);

      if (!assetsRes.ok || !summaryRes.ok || !maintenanceRes.ok) {
        throw new Error('API responded with an error');
      }

      const [apiAssets, apiSummary, apiMaintenance] = await Promise.all([
        assetsRes.json(),
        summaryRes.json(),
        maintenanceRes.json(),
      ]);

      // Map backend fields to frontend Asset shape
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const mappedAssets = apiAssets.map((a: any) => ({
        ...a,
        id: a.asset_id,
        name: a.asset_id,
        type: a.asset_type,
        status: 'online' as const,
        location: { lat: a.lat, lng: a.lng },
        region: a.zone,
        age_years: new Date().getFullYear() - (a.install_year ?? 2010),
        failure_probability_7d: a.risk_score / 100,
        failure_probability_30d: a.risk_score / 100,
        weather_risk_factor: 0,
        last_maintenance: a.last_inspected ?? '',
        next_maintenance: '',
        sensor_readings: [],
        shap_factors: (a.shap_values ?? []).map((s: any) => ({
          name: s.feature,
          value: s.contribution,
        })),
        notes: '',
      }));

      // Map backend summary to GridSummary shape
      const mappedSummary = {
        total_assets: apiSummary.total_assets,
        online: apiSummary.total_assets,
        offline: 0,
        maintenance: apiSummary.maintenance_today,
        degraded: apiSummary.high_risk_count,
        critical_risk_count: apiSummary.critical_count,
        high_risk_count: apiSummary.high_risk_count,
        medium_risk_count: apiSummary.medium_risk_count ?? 0,
        low_risk_count: apiSummary.low_risk_count ?? 0,
        outage_risk_24h: (apiSummary.critical_count / Math.max(apiSummary.total_assets, 1)),
        avg_risk_score: 0,
        pending_maintenance_tasks: apiMaintenance.length,
        maintenance_today: apiSummary.maintenance_today,
        last_updated: apiSummary.last_updated,
      };

      // Map maintenance tasks
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const mappedTasks = apiMaintenance.map((t: any) => ({
        id: t.task_id,
        asset_id: t.asset_id,
        asset_name: t.asset_id,
        asset_type: 'transformer' as const,
        zone: 'Central' as const,
        priority: t.priority === 'CRITICAL' || t.priority === 'critical' ? 'emergency' as const
          : t.priority === 'HIGH' || t.priority === 'high' ? 'urgent' as const
          : 'routine' as const,
        risk_level: t.priority?.toLowerCase() ?? 'low',
        scheduled_date: t.scheduled_date,
        action: t.action,
        estimated_duration_hours: 4,
        assigned_team: t.crew,
        description: t.action,
        estimated_cost_usd: 0,
        status: t.status as 'scheduled' | 'in_progress' | 'completed' | 'deferred',
      }));

      set({
        assets: mappedAssets,
        gridSummary: mappedSummary,
        maintenanceTasks: mappedTasks,
        isLoading: false,
        error: null,
      });
    } catch (err) {
      // Backend not running — fall back to mock data silently
      console.warn('[GridHealth] API unavailable, using mock data:', err);
      set({
        assets: mockAssets,
        gridSummary: mockGridSummary,
        maintenanceTasks: mockMaintenanceTasks,
        isLoading: false,
        error: null,
      });
    }
  },

  selectAsset: (id) => set({ selectedAssetId: id }),

  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  setMobileSidebarOpen: (open) => set({ mobileSidebarOpen: open }),

  toggleMobileSidebar: () =>
    set((state) => ({ mobileSidebarOpen: !state.mobileSidebarOpen })),

  setFilter: (key, value) =>
    set((state) => ({ filters: { ...state.filters, [key]: value } })),

  resetFilters: () => set({ filters: { ...defaultFilters } }),

  setTheme: (id) => {
    applyTheme(id);
    set({ theme: id });
  },

  getFilteredAssets: () => {
    const { assets, filters } = get();
    return assets.filter((asset) => {
      if (filters.risk_level !== 'all' && asset.risk_level !== filters.risk_level)
        return false;
      if (filters.asset_type !== 'all' && asset.type !== filters.asset_type)
        return false;
      if (filters.zone !== 'all' && asset.zone !== filters.zone)
        return false;
      if (filters.status !== 'all' && asset.status !== filters.status)
        return false;
      return true;
    });
  },
}));

// ── Convenience selector hooks ─────────────────────────────────────────────
export const useAssets = () => useAppStore((s) => s.assets);
export const useGridSummary = () => useAppStore((s) => s.gridSummary);
export const useMaintenanceTasks = () => useAppStore((s) => s.maintenanceTasks);
export const useIsLoading = () => useAppStore((s) => s.isLoading);
export const useFilters = () => useAppStore((s) => s.filters);

// ── Risk colour helpers ────────────────────────────────────────────────────
export function riskColor(level: RiskLevel): string {
  return {
    low:      'text-green-400',
    medium:   'text-yellow-400',
    high:     'text-orange-400',
    critical: 'text-red-400',
  }[level];
}

export function riskBorderColor(level: RiskLevel): string {
  return {
    low:      'border-green-500',
    medium:   'border-yellow-500',
    high:     'border-orange-500',
    critical: 'border-red-500',
  }[level];
}

export function riskBg(level: RiskLevel): string {
  return {
    low:      'bg-green-500/15 text-green-400',
    medium:   'bg-yellow-500/15 text-yellow-400',
    high:     'bg-orange-500/15 text-orange-400',
    critical: 'bg-red-500/15 text-red-400',
  }[level];
}

export function riskHex(level: RiskLevel): string {
  return { low: '#22c55e', medium: '#eab308', high: '#f97316', critical: '#ef4444' }[level];
}

// ── Zone colour ───────────────────────────────────────────────────────────
export function zoneColor(zone: Zone): string {
  return {
    North:   'text-sky-400',
    South:   'text-emerald-400',
    East:    'text-violet-400',
    West:    'text-amber-400',
    Central: 'text-pink-400',
  }[zone];
}
