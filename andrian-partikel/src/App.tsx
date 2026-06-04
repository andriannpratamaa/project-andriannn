import React from 'react';
import Scene from './components/Scene';
import UIOverlay from './components/UIOverlay';
import GestureHandler from './components/GestureHandler';

function App() {
  return (
    <div className="w-screen h-screen overflow-hidden bg-black relative">
      <Scene />
      <UIOverlay />
      <GestureHandler />
    </div>
  );
}

export default App;
