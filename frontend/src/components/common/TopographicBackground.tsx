import React, { memo, useEffect, useRef } from 'react';
import cinematicTopoBg from '../../assets/cinematic_topo_bg.jpg';

/**
 * TopographicBackground
 * 
 * Cinematic Flowing Topographic Atmosphere (Reference Image 2):
 * - Sculptural, organic flowing dunes and folded ridges spanning the entire viewport
 * - Warm champagne and copper sunset illumination on the crests (#E9D2B7, #D9825B, #F8E5D0)
 * - Deep velvety midnight-blue shadows in the valleys (#06080E, #090D16, #101526)
 * - Cool slate-cyan mist in the upper-right atmosphere (#9FBBC9, #5EB2B8)
 * - Dynamic living ridge shimmer paths and volumetric billowing mist
 * - Pointer-responsive warm champagne specular illumination (lerp-interpolated)
 * - Central readability vignette protecting developer text and diff contrast
 */
export const TopographicBackground: React.FC = memo(() => {
  const pointerLightRef = useRef<HTMLDivElement>(null);

  // Smooth pointer-responsive illumination on desktop (disabled when prefers-reduced-motion is active)
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return;
    }

    let targetX = window.innerWidth / 2;
    let targetY = window.innerHeight / 3;
    let currentX = targetX;
    let currentY = targetY;
    let animationFrameId: number;
    let isTracking = false;

    const handleMouseMove = (e: MouseEvent) => {
      targetX = e.clientX;
      targetY = e.clientY;
      if (!isTracking) {
        isTracking = true;
        animate();
      }
    };

    const animate = () => {
      // Smooth lerp interpolation for fluid, lag-free floating light
      currentX += (targetX - currentX) * 0.035;
      currentY += (targetY - currentY) * 0.035;

      if (pointerLightRef.current) {
        pointerLightRef.current.style.transform = `translate3d(${currentX - 250}px, ${currentY - 250}px, 0)`;
      }

      if (Math.abs(targetX - currentX) > 0.5 || Math.abs(targetY - currentY) > 0.5) {
        animationFrameId = requestAnimationFrame(animate);
      } else {
        isTracking = false;
      }
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div
      className="fixed inset-0 pointer-events-none select-none overflow-hidden z-0"
      aria-hidden="true"
    >
      {/* 1. Deep Midnight Blue-Black Base Foundation */}
      <div className="absolute inset-0 bg-[#06080E]" />

      {/* 2. Primary Layer: Cinematic Flowing Terrain Wallpaper (From Reference Image 2) */}
      <div className="absolute inset-0 overflow-hidden">
        <img
          src={cinematicTopoBg}
          alt=""
          className="w-full h-full object-cover object-center scale-[1.03] animate-ambient-slow opacity-90 transition-opacity duration-1000"
          style={{
            filter: 'contrast(1.08) saturate(1.15) brightness(0.96)',
            willChange: 'transform',
          }}
        />
      </div>

      {/* 3. Volumetric Atmospheric Light Fields (Directional Warm & Cool Cinematic Lighting) */}
      <div className="absolute inset-0 overflow-hidden mix-blend-screen pointer-events-none">
        {/* Upper-Left Golden & Copper Ridge Illumination */}
        <div
          className="absolute -top-[10%] -left-[10%] w-[70vw] h-[70vw] max-w-[1200px] max-h-[1200px] rounded-full blur-[110px] opacity-50 animate-ambient-slow"
          style={{
            background:
              'radial-gradient(circle, rgba(226, 140, 92, 0.42) 0%, rgba(248, 229, 208, 0.25) 30%, rgba(184, 94, 58, 0.15) 55%, transparent 80%)',
          }}
        />

        {/* Upper-Center Champagne Crest Light */}
        <div
          className="absolute -top-[15%] left-[30%] w-[50vw] h-[45vw] max-w-[900px] max-h-[750px] rounded-full blur-[90px] opacity-40 animate-ambient-reverse"
          style={{
            background:
              'radial-gradient(ellipse, rgba(248, 229, 208, 0.35) 0%, rgba(217, 154, 120, 0.18) 45%, transparent 75%)',
          }}
        />

        {/* Upper-Right Cool Slate-Cyan Atmospheric Mist */}
        <div
          className="absolute top-[2%] -right-[8%] w-[60vw] h-[60vw] max-w-[1000px] max-h-[1000px] rounded-full blur-[120px] opacity-45 animate-mist-drift"
          style={{
            background:
              'radial-gradient(circle, rgba(94, 178, 184, 0.35) 0%, rgba(184, 201, 216, 0.22) 35%, rgba(16, 26, 42, 0.2) 65%, transparent 85%)',
          }}
        />

        {/* Lower Valleys Deep Bronze Accent */}
        <div
          className="absolute -bottom-[20%] right-[10%] w-[65vw] h-[50vw] max-w-[1100px] max-h-[800px] rounded-full blur-[130px] opacity-30 animate-ambient-slow"
          style={{
            background:
              'radial-gradient(ellipse, rgba(217, 130, 91, 0.25) 0%, rgba(158, 112, 91, 0.15) 45%, transparent 75%)',
          }}
        />

        {/* Pointer-Tracking Ethereal Champagne Highlight Orb (Desktop) */}
        <div
          ref={pointerLightRef}
          className="absolute top-0 left-0 w-[500px] h-[500px] rounded-full blur-[90px] opacity-35 transition-opacity duration-700 hidden md:block"
          style={{
            background:
              'radial-gradient(circle, rgba(248, 229, 208, 0.32) 0%, rgba(217, 130, 91, 0.15) 38%, transparent 70%)',
            transform: 'translate3d(50vw, 30vh, 0)',
            willChange: 'transform',
          }}
        />
      </div>

      {/* 4. Fine Luminous SVG Ridge Shimmer Paths (Accent Contours Tracing the Dunes) */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none opacity-80"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 1920 1080"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          <filter id="topoGlowWarm" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          {/* Warm Champagne to Copper Contour Gradient */}
          <linearGradient id="champagneContourGrad" x1="0%" y1="0%" x2="100%" y2="80%">
            <stop offset="0%" stopColor="#F8E5D0" stopOpacity="0.85" />
            <stop offset="30%" stopColor="#E9D2B7" stopOpacity="0.65" />
            <stop offset="65%" stopColor="#D9825B" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#202A3A" stopOpacity="0.1" />
          </linearGradient>

          {/* Cool Slate-Cyan Contour Gradient */}
          <linearGradient id="coolMistContourGrad" x1="100%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#B8C9D8" stopOpacity="0.75" />
            <stop offset="45%" stopColor="#5EB2B8" stopOpacity="0.45" />
            <stop offset="85%" stopColor="#101526" stopOpacity="0.1" />
          </linearGradient>

          {/* Dynamic Living Shimmer Beam Gradient */}
          <linearGradient id="ridgeShimmerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#D9825B" stopOpacity="0" />
            <stop offset="50%" stopColor="#F8E5D0" stopOpacity="0.95" />
            <stop offset="100%" stopColor="#E9D2B7" stopOpacity="0" />
          </linearGradient>
        </defs>

        <g fill="none">
          {/* Luminous Ridge 1: Upper-left flowing dune crest */}
          <path
            d="M-50,80 C320,120 480,340 760,260 C1040,180 1360,60 1720,110 C1860,130 1980,180 2050,220"
            stroke="url(#champagneContourGrad)"
            strokeWidth="1.6"
            filter="url(#topoGlowWarm)"
          />

          {/* Shimmer beam traveling along Ridge 1 */}
          <path
            d="M-50,80 C320,120 480,340 760,260 C1040,180 1360,60 1720,110 C1860,130 1980,180 2050,220"
            stroke="url(#ridgeShimmerGrad)"
            strokeWidth="2.4"
            strokeDasharray="220 1300"
            className="animate-shimmer-ridge"
          />

          {/* Luminous Ridge 2: Mid-left sweep into central fold */}
          <path
            d="M-60,320 C180,380 380,590 680,520 C980,450 1280,310 1620,380 C1820,420 1980,520 2050,560"
            stroke="url(#champagneContourGrad)"
            strokeWidth="1.2"
            opacity="0.65"
          />

          {/* Luminous Ridge 3: Northeast cool mist contour */}
          <path
            d="M1200,40 C1440,140 1680,180 1880,140 C1980,120 2040,160 2080,190"
            stroke="url(#coolMistContourGrad)"
            strokeWidth="1.4"
            filter="url(#topoGlowWarm)"
          />

          {/* Shimmer beam traveling in reverse along Ridge 3 */}
          <path
            d="M1200,40 C1440,140 1680,180 1880,140 C1980,120 2040,160 2080,190"
            stroke="url(#ridgeShimmerGrad)"
            strokeWidth="2.2"
            strokeDasharray="160 980"
            className="animate-shimmer-ridge-reverse"
          />

          {/* Fine subtle elevation striations */}
          <path
            d="M-50,140 C330,180 490,400 770,320 C1050,240 1370,120 1730,170"
            stroke="url(#champagneContourGrad)"
            strokeWidth="0.8"
            opacity="0.45"
          />
          <path
            d="M-50,200 C340,240 500,460 780,380 C1060,300 1380,180 1740,230"
            stroke="url(#champagneContourGrad)"
            strokeWidth="0.8"
            opacity="0.35"
          />
        </g>
      </svg>

      {/* 5. Central Atmospheric Readability Vignette (Protecting Text & Code Contrast) */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse 75% 65% at 50% 45%, rgba(6, 8, 14, 0.58) 0%, rgba(6, 8, 14, 0.35) 60%, transparent 95%)',
        }}
      />

      {/* Top & Bottom Cinematic Border Transitions */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'linear-gradient(to bottom, rgba(6, 8, 14, 0.45) 0%, transparent 15%, transparent 82%, rgba(6, 8, 14, 0.85) 100%)',
        }}
      />

      {/* 6. Micro-Grain Texture (Prevents gradient banding on OLED & high-resolution displays) */}
      <svg
        className="absolute inset-0 w-full h-full opacity-[0.025] mix-blend-screen pointer-events-none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <filter id="cinematicGrain">
          <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#cinematicGrain)" />
      </svg>
    </div>
  );
});

TopographicBackground.displayName = 'TopographicBackground';
