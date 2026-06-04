import { create } from 'zustand';

export type GestureType = 'open' | 'closed' | 'victory' | 'metal' | 'none';

interface AppState {
  // Gesture State
  handOpenness: number;
  isHandDetected: boolean;
  handPosition: { x: number, y: number }; // -1 to 1
  gestureType: GestureType;
  
  // Visual Customization
  particleColor: string;
  
  // UI State
  isFullscreen: boolean;
  
  // Actions
  setHandState: (openness: number, detected: boolean, position: { x: number, y: number }, type: GestureType) => void;
  toggleFullscreen: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  handOpenness: 1,
  isHandDetected: false,
  handPosition: { x: 0, y: 0 },
  gestureType: 'none',
  
  particleColor: '#0088ff', // Blue default
  
  isFullscreen: false,
  
  setHandState: (openness, detected, position, type) => set({ 
    handOpenness: openness, 
    isHandDetected: detected, 
    handPosition: position,
    gestureType: type
  }),
  toggleFullscreen: () => set((state) => ({ isFullscreen: !state.isFullscreen })),
}));
