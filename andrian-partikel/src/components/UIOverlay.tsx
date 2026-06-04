import React from 'react';
import { useAppStore } from '../store/useAppStore';
import { Maximize, Minimize, Hand } from 'lucide-react';

const UIOverlay: React.FC = () => {
  const { 
    isHandDetected, 
    gestureType,
    isFullscreen, 
    toggleFullscreen 
  } = useAppStore();

  const handleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      toggleFullscreen();
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
        toggleFullscreen();
      }
    }
  };

  const getGestureLabel = () => {
    if (!isHandDetected) return 'No Hand';
    switch (gestureType) {
      case 'closed': return 'Galaxy Mode';
      case 'open': return 'Explosion';
      case 'victory': return 'Love Mode';
      case 'metal': return 'Heart Beat';
      default: return 'Detected';
    }
  };

  return (
    <div className="absolute inset-0 pointer-events-none flex flex-col justify-between p-6 z-10">
      {/* Header */}
      <div className="flex justify-between items-start pointer-events-auto">
        <div>
          <h1 className="text-2xl font-bold text-blue-500 tracking-wider drop-shadow-[0_0_10px_rgba(0,100,255,0.8)]">ANDRIAN</h1>
          <p className="text-xs text-blue-300/70 uppercase tracking-widest">Gesture Particle System</p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full border ${isHandDetected ? 'border-blue-500/50 bg-blue-500/10 text-blue-400' : 'border-red-500/50 bg-red-500/10 text-red-400'} transition-colors backdrop-blur-md`}>
            <Hand size={14} />
            <span className="text-xs font-medium uppercase min-w-[80px] text-center">
              {getGestureLabel()}
            </span>
          </div>
          
          <button 
            onClick={handleFullscreen}
            className="p-2 rounded-full bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/30 transition-colors backdrop-blur-md"
          >
            {isFullscreen ? <Minimize size={20} /> : <Maximize size={20} />}
          </button>
        </div>
      </div>

      {/* Footer Removed as requested */}
    </div>
  );
};

export default UIOverlay;