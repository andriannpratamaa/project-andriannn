import React, { useEffect, useRef, useState } from 'react';
import { FilesetResolver, HandLandmarker } from '@mediapipe/tasks-vision';
import { useAppStore, GestureType } from '../store/useAppStore';

const GestureHandler: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [loaded, setLoaded] = useState(false);
  const { setHandState } = useAppStore();
  const lastVideoTimeRef = useRef(-1);
  const requestRef = useRef<number>(0);
  const handLandmarkerRef = useRef<HandLandmarker | null>(null);

  useEffect(() => {
    const initHandLandmarker = async () => {
      try {
        const vision = await FilesetResolver.forVisionTasks(
          'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/wasm'
        );
        
        handLandmarkerRef.current = await HandLandmarker.createFromOptions(vision, {
          baseOptions: {
            modelAssetPath: `https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task`,
            delegate: 'GPU',
          },
          runningMode: 'VIDEO',
          numHands: 1,
        });
        setLoaded(true);
      } catch (error) {
        console.error("Error initializing hand landmarker:", error);
      }
    };

    initHandLandmarker();

    return () => {
      if (handLandmarkerRef.current) {
        handLandmarkerRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (!loaded || !videoRef.current) return;

    const enableCam = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.addEventListener('loadeddata', predictWebcam);
        }
      } catch (err) {
        console.error("Error accessing webcam:", err);
      }
    };

    enableCam();

    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream;
        stream.getTracks().forEach(track => track.stop());
      }
      cancelAnimationFrame(requestRef.current);
    };
  }, [loaded]);

  const predictWebcam = () => {
    if (!handLandmarkerRef.current || !videoRef.current) return;

    const video = videoRef.current;
    if (video.currentTime !== lastVideoTimeRef.current) {
      lastVideoTimeRef.current = video.currentTime;
      
      const startTimeMs = performance.now();
      const results = handLandmarkerRef.current.detectForVideo(video, startTimeMs);

      if (results.landmarks && results.landmarks.length > 0) {
        const landmarks = results.landmarks[0];
        
        // 1. Calculate Hand Position (Center)
        const wrist = landmarks[0];
        const middleMCP = landmarks[9];
        
        const rawX = (wrist.x + middleMCP.x) / 2;
        const rawY = (wrist.y + middleMCP.y) / 2;
        
        const posX = (rawX - 0.5) * 2; 
        const posY = -(rawY - 0.5) * 2; 

        // 2. Calculate Openness & Gesture Type
        const handSize = Math.sqrt(
          Math.pow(middleMCP.x - wrist.x, 2) + 
          Math.pow(middleMCP.y - wrist.y, 2)
        );

        const isExtended = (tipIdx: number, pipIdx: number) => {
          const tip = landmarks[tipIdx];
          const pip = landmarks[pipIdx];
          const distTip = Math.sqrt(Math.pow(tip.x - wrist.x, 2) + Math.pow(tip.y - wrist.y, 2));
          const distPip = Math.sqrt(Math.pow(pip.x - wrist.x, 2) + Math.pow(pip.y - wrist.y, 2));
          return distTip > distPip * 1.2; 
        };

        const indexExt = isExtended(8, 6);
        const middleExt = isExtended(12, 10);
        const ringExt = isExtended(16, 14);
        const pinkyExt = isExtended(20, 18);

        let type: GestureType = 'open';
        let openness = 1;

        if (indexExt && !middleExt && !ringExt && pinkyExt) {
          type = 'metal'; // Metal / Rock
          openness = 0.5;
        } else if (indexExt && middleExt && !ringExt && !pinkyExt) {
          type = 'victory';
          openness = 0.8;
        } else if (!indexExt && !middleExt && !ringExt && !pinkyExt) {
          type = 'closed';
          openness = 0;
        } else {
          const tips = [8, 12, 16, 20];
          let totalDist = 0;
          tips.forEach(t => {
            const d = Math.sqrt(
              Math.pow(landmarks[t].x - wrist.x, 2) + 
              Math.pow(landmarks[t].y - wrist.y, 2)
            );
            totalDist += d;
          });
          const avg = totalDist / 4;
          const ratio = avg / handSize;
          openness = Math.max(0, Math.min(1, (ratio - 0.8) / 1.0));
          type = openness > 0.5 ? 'open' : 'closed';
        }

        setHandState(openness, true, { x: posX, y: posY }, type);
        
      } else {
        setHandState(0, false, { x: 0, y: 0 }, 'none');
      }
    }
    
    requestRef.current = requestAnimationFrame(predictWebcam);
  };

  return (
    <div className="fixed bottom-8 left-8 w-96 h-72 rounded-2xl overflow-hidden border-4 border-blue-500/30 shadow-2xl z-50 bg-black/80 backdrop-blur-md transition-all duration-300 hover:scale-105">
      {!loaded && <div className="absolute inset-0 flex items-center justify-center text-sm text-blue-400 animate-pulse">Initializing AI...</div>}
      <video 
        ref={videoRef} 
        className="w-full h-full object-cover transform -scale-x-100 opacity-80" 
        autoPlay 
        playsInline 
        muted
      />
      <div className="absolute bottom-2 left-0 right-0 text-center text-[10px] text-blue-300/70 font-mono uppercase tracking-widest">
        ANDRIAN VISION
      </div>
    </div>
  );
};

export default GestureHandler;
