import React, { memo, useEffect, useRef } from 'react';

/**
 * TopographicBackground
 * 
 * Living Topographic Intelligence Atmosphere:
 * - Deep graphite foundation (#07090E, #0B1019)
 * - Art-directed asymmetrical atmospheric light fields (steel-blue #17283D, icy-blue #64C7FF, pale mist #A8DFFF)
 * - Multi-tiered luminous vector elevation contours with distinct index contours and summit peaks
 * - Living ambient ridge beam pulse and smooth, throttled pointer-responsive illumination
 * - Fine tactile grain to prevent digital gradient banding
 * - Central contrast calibration ensuring developer-grade readability
 */
export const TopographicBackground: React.FC = memo(() => {
  const pointerLightRef = useRef<HTMLDivElement>(null);

  // Smooth pointer-responsive illumination on desktop (disabled when prefers-reduced-motion is active)
  useEffect(() => {
    // Check if reduced motion is requested
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

      // Continue animating until settled
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
      {/* 1. Deep Graphite Foundation */}
      <div className="absolute inset-0 bg-[#07090E]" />

      {/* 2. Layer A: Asymmetrical Atmospheric Light Fields */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Upper-Left Major Light Basin: Steel-blue and icy-blue glow */}
        <div
          className="absolute -top-[12%] -left-[8%] w-[65vw] h-[65vw] max-w-[1100px] max-h-[1100px] rounded-full blur-[100px] opacity-45 animate-ambient-slow"
          style={{
            background:
              'radial-gradient(circle, rgba(100, 199, 255, 0.24) 0%, rgba(23, 40, 61, 0.45) 45%, rgba(11, 16, 25, 0.1) 75%, transparent 100%)',
          }}
        />

        {/* Upper-Right Highland Illumination: Pale mist and cyan aura */}
        <div
          className="absolute top-[8%] -right-[12%] w-[55vw] h-[55vw] max-w-[950px] max-h-[950px] rounded-full blur-[110px] opacity-35 animate-ambient-reverse"
          style={{
            background:
              'radial-gradient(circle, rgba(53, 213, 242, 0.22) 0%, rgba(168, 223, 255, 0.12) 35%, rgba(17, 26, 40, 0.35) 60%, transparent 85%)',
          }}
        />

        {/* Southern Flank Atmospheric Wash: Deep steel-blue depth */}
        <div
          className="absolute -bottom-[25%] left-[15%] w-[70vw] h-[55vw] max-w-[1200px] max-h-[850px] rounded-full blur-[120px] opacity-30 animate-ambient-slow"
          style={{
            background:
              'radial-gradient(circle, rgba(100, 199, 255, 0.18) 0%, rgba(23, 40, 61, 0.4) 50%, transparent 80%)',
          }}
        />

        {/* Smooth pointer-tracking ethereal ambient light orb (desktop) */}
        <div
          ref={pointerLightRef}
          className="absolute top-0 left-0 w-[500px] h-[500px] rounded-full blur-[90px] opacity-30 transition-opacity duration-700 hidden md:block"
          style={{
            background:
              'radial-gradient(circle, rgba(100, 199, 255, 0.25) 0%, rgba(53, 213, 242, 0.1) 40%, transparent 70%)',
            transform: 'translate3d(50vw, 30vh, 0)',
            willChange: 'transform',
          }}
        />
      </div>

      {/* 3. Layer B: Visibly Luminous Topographic Contour Landscape */}
      <svg
        className="absolute inset-0 w-full h-full"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 1920 1080"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          {/* Subtle glow filter for luminous index contours */}
          <filter id="topoGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          {/* Icy Blue to Steel Blue Contour Gradient 1 */}
          <linearGradient id="luminousContour1" x1="0%" y1="0%" x2="100%" y2="80%">
            <stop offset="0%" stopColor="#64C7FF" stopOpacity="0.85" />
            <stop offset="35%" stopColor="#35D5F2" stopOpacity="0.65" />
            <stop offset="70%" stopColor="#17283D" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#64C7FF" stopOpacity="0.15" />
          </linearGradient>

          {/* Pale Mist to Steel Gradient 2 */}
          <linearGradient id="luminousContour2" x1="100%" y1="20%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#A8DFFF" stopOpacity="0.8" />
            <stop offset="40%" stopColor="#64C7FF" stopOpacity="0.55" />
            <stop offset="80%" stopColor="#17283D" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#0B1019" stopOpacity="0.05" />
          </linearGradient>

          {/* Subtle Intermediate Gradient */}
          <linearGradient id="intermediateContour" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#64C7FF" stopOpacity="0.3" />
            <stop offset="50%" stopColor="#A8DFFF" stopOpacity="0.18" />
            <stop offset="100%" stopColor="#17283D" stopOpacity="0.1" />
          </linearGradient>

          {/* Shimmer gradient for animated living ridge pulse */}
          <linearGradient id="ridgePulseGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#64C7FF" stopOpacity="0" />
            <stop offset="50%" stopColor="#35D5F2" stopOpacity="0.95" />
            <stop offset="100%" stopColor="#A8DFFF" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* ---------------- REGION 1: NORTHERN RIDGE SYSTEM ---------------- */}
        <g fill="none">
          {/* Contour 01 (Deep valley base) */}
          <path
            d="M-60,110 C340,30 680,240 1080,130 C1460,20 1780,180 2040,110"
            stroke="url(#intermediateContour)"
            strokeWidth="0.9"
          />

          {/* Contour 02 */}
          <path
            d="M-60,155 C350,75 700,285 1105,175 C1485,65 1805,225 2040,155"
            stroke="url(#intermediateContour)"
            strokeWidth="0.9"
          />

          {/* Contour 03 */}
          <path
            d="M-60,205 C360,125 720,335 1135,225 C1515,115 1835,275 2040,205"
            stroke="url(#intermediateContour)"
            strokeWidth="1.1"
          />

          {/* Contour 04: LUMINOUS INDEX CONTOUR [ELEV 650M] */}
          <path
            d="M-60,260 C375,180 745,390 1170,280 C1550,170 1870,330 2040,260"
            stroke="url(#luminousContour1)"
            strokeWidth="1.8"
            filter="url(#topoGlow)"
          />

          {/* Living Shimmer Beam pulsing along Index Contour 04 */}
          <path
            d="M-60,260 C375,180 745,390 1170,280 C1550,170 1870,330 2040,260"
            stroke="url(#ridgePulseGrad)"
            strokeWidth="2.5"
            strokeDasharray="180 1200"
            className="animate-shimmer-ridge"
          />

          {/* Contour 05 */}
          <path
            d="M-60,320 C390,240 770,450 1210,340 C1590,230 1910,390 2040,320"
            stroke="url(#intermediateContour)"
            strokeWidth="0.9"
          />

          {/* Contour 06 */}
          <path
            d="M-60,385 C410,305 800,515 1255,405 C1635,295 1955,455 2040,385"
            stroke="url(#intermediateContour)"
            strokeWidth="1.0"
          />

          {/* Contour 07 */}
          <path
            d="M-60,455 C430,375 830,585 1305,475 C1685,365 2005,525 2040,455"
            stroke="url(#intermediateContour)"
            strokeWidth="0.9"
          />

          {/* Contour 08: LUMINOUS INDEX CONTOUR [ELEV 500M] */}
          <path
            d="M-60,530 C450,450 865,660 1360,550 C1740,440 2040,600 2060,530"
            stroke="url(#luminousContour1)"
            strokeWidth="1.6"
            filter="url(#topoGlow)"
          />
        </g>

        {/* ---------------- REGION 2: EASTERN HIGHLAND PEAK (Concentric Plateau) ---------------- */}
        <g fill="none">
          {/* Base ring */}
          <path
            d="M1360,-40 C1440,140 1620,230 1790,190 C1920,160 2010,70 2060,-40"
            stroke="url(#intermediateContour)"
            strokeWidth="1.0"
          />

          {/* Tier 2 */}
          <path
            d="M1420,-40 C1490,110 1650,185 1810,150 C1930,120 2010,50 2060,-40"
            stroke="url(#intermediateContour)"
            strokeWidth="1.1"
          />

          {/* Tier 3: LUMINOUS HIGHLAND CREST [SUMMIT +820M] */}
          <path
            d="M1490,-40 C1550,80 1690,140 1835,110 C1935,90 2000,30 2040,-40"
            stroke="url(#luminousContour2)"
            strokeWidth="2.0"
            filter="url(#topoGlow)"
          />

          {/* Summit apex ring */}
          <path
            d="M1570,-40 C1620,50 1730,95 1860,75 C1930,60 1970,10 2000,-40"
            stroke="url(#luminousContour2)"
            strokeWidth="1.3"
          />
        </g>

        {/* ---------------- REGION 3: VALLEY BASIN & SOUTHWEST FLANKS ---------------- */}
        <g fill="none">
          {/* Southern Ridge 01 */}
          <path
            d="M-60,620 C180,600 360,740 540,750 C730,760 900,660 1140,710 C1370,760 1560,920 1760,960 C1940,990 2020,950 2060,930"
            stroke="url(#intermediateContour)"
            strokeWidth="0.9"
          />

          {/* Southern Ridge 02 */}
          <path
            d="M-60,695 C200,675 390,805 580,815 C770,825 940,725 1190,775 C1420,825 1610,985 1810,1025 C1960,1050 2020,1020 2060,1000"
            stroke="url(#intermediateContour)"
            strokeWidth="1.0"
          />

          {/* Southern Ridge 03: LUMINOUS VALLEY ESCARPMENT [ELEV 350M] */}
          <path
            d="M-60,775 C220,755 425,875 625,885 C815,895 985,795 1245,845 C1475,895 1665,1055 1865,1095 C2000,1120 2040,1080 2060,1065"
            stroke="url(#luminousContour1)"
            strokeWidth="1.8"
            filter="url(#topoGlow)"
          />

          {/* Living shimmer along southern escarpment */}
          <path
            d="M-60,775 C220,755 425,875 625,885 C815,895 985,795 1245,845 C1475,895 1665,1055 1865,1095 C2000,1120 2040,1080 2060,1065"
            stroke="url(#ridgePulseGrad)"
            strokeWidth="2.2"
            strokeDasharray="140 1000"
            className="animate-shimmer-ridge-reverse"
          />

          {/* Southern Ridge 04 */}
          <path
            d="M-60,860 C240,840 460,945 670,955 C860,965 1030,865 1300,915 C1530,965 1720,1125 1920,1165"
            stroke="url(#intermediateContour)"
            strokeWidth="0.9"
          />

          {/* Southern Ridge 05 */}
          <path
            d="M-60,950 C260,930 500,1020 720,1030 C910,1040 1080,940 1360,990 C1590,1040 1780,1195 1980,1235"
            stroke="url(#intermediateContour)"
            strokeWidth="1.2"
          />
        </g>

        {/* ---------------- REGION 4: ILLUMINATED NODES & GEODETIC METRICS ---------------- */}
        {/* Luminous elevation points / summit crosses */}
        <g stroke="#64C7FF" fill="none" opacity="0.75">
          {/* North Ridge Index Point */}
          <circle cx="1170" cy="280" r="3.5" fill="#35D5F2" filter="url(#topoGlow)" />
          <circle cx="1170" cy="280" r="8" stroke="#64C7FF" strokeWidth="0.8" strokeDasharray="2 3" />

          {/* East Plateau Summit Node */}
          <circle cx="1835" cy="110" r="4" fill="#A8DFFF" filter="url(#topoGlow)" />
          <circle cx="1835" cy="110" r="9" stroke="#35D5F2" strokeWidth="0.8" strokeDasharray="3 3" />

          {/* South Valley Landmark Node */}
          <circle cx="625" cy="885" r="3" fill="#64C7FF" filter="url(#topoGlow)" />
          <circle cx="625" cy="885" r="7" stroke="#A8DFFF" strokeWidth="0.75" />

          {/* Precision crosshairs */}
          <path d="M1160,280 L1180,280 M1170,270 L1170,290" strokeWidth="0.8" />
          <path d="M1825,110 L1845,110 M1835,100 L1835,120" strokeWidth="0.8" />
          <path d="M615,885 L635,885 M625,875 L625,895" strokeWidth="0.8" />
        </g>

        {/* Luminous Typography & Elevation Labels */}
        <g
          className="font-mono select-none"
          fill="#A8DFFF"
          fontSize="10"
          letterSpacing="0.12em"
          opacity="0.65"
        >
          <text x="1190" y="284">ELEV +650M // INDEX CREST 04</text>
          <text x="1740" y="85">SUMMIT +820M // PEAK 01</text>
          <text x="645" y="889">BASIN +350M // CONTOUR ESCARPMENT</text>
          <text x="140" y="150" fill="#64C7FF" opacity="0.45">LAT 41° 18&apos; N // LON 72° 55&apos; W</text>
          <text x="1550" y="620" fill="#64C7FF" opacity="0.35">CONTOUR INTERVAL: 25M [AUTONOMOUS TERRAIN]</text>
        </g>
      </svg>

      {/* 4. Layer C: Atmospheric Depth Vignette & Readability Calibration */}
      {/* Soft center darkness protecting dashboard text while letting contours frame the workspace */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse 70% 60% at 50% 38%, rgba(7, 9, 14, 0.42) 0%, rgba(7, 9, 14, 0.72) 65%, rgba(7, 9, 14, 0.94) 100%)',
        }}
      />

      {/* Fine Directional Illumination Tint (NW to SE) */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'linear-gradient(135deg, rgba(100, 199, 255, 0.05) 0%, transparent 45%, rgba(23, 40, 61, 0.25) 100%)',
        }}
      />

      {/* 5. Layer D: Fine Technical Texture (Subtle Noise Matrix to prevent gradient banding) */}
      <svg
        className="absolute inset-0 w-full h-full opacity-[0.03] mix-blend-screen pointer-events-none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <filter id="topoNoise">
          <feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="3" stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#topoNoise)" />
      </svg>
    </div>
  );
});

TopographicBackground.displayName = 'TopographicBackground';
