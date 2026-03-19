import { create } from 'zustand';

interface LabState {
  // Current epoch for history map
  currentEpochId: string | null;
  setCurrentEpochId: (id: string | null) => void;

  // Map state
  mapCenter: [number, number];
  mapZoom: number;
  setMapView: (center: [number, number], zoom: number) => void;

  // Selected marker
  selectedMarkerId: string | null;
  setSelectedMarkerId: (id: string | null) => void;

  // Sidebar open state
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

export const useLabStore = create<LabState>((set) => ({
  currentEpochId: null,
  setCurrentEpochId: (id) => set({ currentEpochId: id }),

  // Center of Kazakhstan
  mapCenter: [48.0196, 66.9237],
  mapZoom: 5,
  setMapView: (center, zoom) => set({ mapCenter: center, mapZoom: zoom }),

  selectedMarkerId: null,
  setSelectedMarkerId: (id) => set({ selectedMarkerId: id }),

  sidebarOpen: false,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
}));
