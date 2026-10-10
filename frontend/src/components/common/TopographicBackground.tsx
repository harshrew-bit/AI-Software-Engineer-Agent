import React, { memo } from 'react';

/**
 * TopographicBackground
 * 
 * Bespoke multi-layered topographic terrain canvas with cool atmospheric lighting,
 * flowing vector contour lines, elevation index marks, and slow ambient motion.
 * Designed with a deep graphite center to ensure maximum developer-tool readability.
 */
export const TopographicBackground: React.FC = memo(() => {
  return (
    <div
      className="fixed inset-0 pointer-events-none select-none overflow-hidden z-0"
      aria-hidden="true"
    >
      {/* 1. Deep Graphite Foundation */}
      <div className="absolute inset-0 bg-[#07090e]" />

      {/* 2. Atmospheric Ambient Light Fields (Slow Drifting GPU Orbs) */}
      <div className="absolute inset-0 overflow-hidden opacity-90">
        {/* Cool steel-blue upper-left lighting field */}
        <div
          className="absolute -top-[15%] -left-[10%] w-[55vw] h-[55vw] rounded-full blur-[110px] opacity-25 animate-ambient-slow"
          style={{
            background: 'radial-gradient(circle, rgba(56, 189, 248, 0.28) 0%, rgba(30, 58, 95, 0.2) 50%, transparent 75%)',
          }}
        />

        {/* Misty slate-grey / steel illumination orb on the right */}
        <div
          className="absolute top-[20%] -right-[15%] w-[50vw] h-[50vw] rounded-full blur-[120px] opacity-20 animate-ambient-reverse"
          style={{
            background: 'radial-gradient(circle, rgba(148, 163, 184, 0.22) 0%, rgba(31, 48, 74, 0.2) 55%, transparent 75%)',
          }}
        />

        {/* Deep bottom terrain shadow with faint cyan-silver crest glow */}
        <div
          className="absolute -bottom-[20%] left-[20%] w-[60vw] h-[45vw] rounded-full blur-[130px] opacity-15 animate-ambient-slow"
          style={{
            background: 'radial-gradient(circle, rgba(56, 189, 248, 0.18) 0%, rgba(15, 23, 42, 0.4) 60%, transparent 80%)',
          }}
        />
      </div>

      {/* 3. Deep Topographic Vector Terrain Layer (Large scale contour lines) */}
      <svg
        className="absolute inset-0 w-full h-full opacity-20"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 1920 1080"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          <linearGradient id="contourGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.4" />
            <stop offset="50%" stopColor="#64748b" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#1e293b" stopOpacity="0.05" />
          </linearGradient>
          <linearGradient id="contourGrad2" x1="100%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#94a3b8" stopOpacity="0.3" />
            <stop offset="60%" stopColor="#38bdf8" stopOpacity="0.1" />
            <stop offset="100%" stopColor="#0f172a" stopOpacity="0.02" />
          </linearGradient>
        </defs>

        {/* Flowing background macro-contour bands */}
        <path
          d="M-100,250 C320,120 680,380 1100,210 C1450,80 1780,240 2100,160"
          fill="none"
          stroke="url(#contourGrad1)"
          strokeWidth="1.2"
          strokeDasharray="4 8"
        />
        <path
          d="M-100,320 C340,190 710,440 1140,280 C1500,150 1820,310 2100,230"
          fill="none"
          stroke="url(#contourGrad1)"
          strokeWidth="1.4"
        />
        <path
          d="M-100,410 C380,280 750,520 1190,370 C1560,250 1870,390 2100,320"
          fill="none"
          stroke="url(#contourGrad1)"
          strokeWidth="1.8"
        />
        <path
          d="M-100,510 C410,390 800,610 1240,470 C1620,360 1910,480 2100,420"
          fill="none"
          stroke="url(#contourGrad2)"
          strokeWidth="1.2"
        />
        <path
          d="M-100,630 C450,510 860,720 1310,590 C1690,490 1950,590 2100,540"
          fill="none"
          stroke="url(#contourGrad2)"
          strokeWidth="1.5"
        />
        <path
          d="M-100,770 C500,660 930,850 1390,730 C1760,640 1990,720 2100,670"
          fill="none"
          stroke="url(#contourGrad1)"
          strokeWidth="1.2"
          strokeDasharray="6 12"
        />
        <path
          d="M-100,920 C560,820 1010,990 1480,880 C1840,800 2030,860 2100,820"
          fill="none"
          stroke="url(#contourGrad2)"
          strokeWidth="1.6"
        />
      </svg>

      {/* 4. Fine Generative Topographic Elevation Contours & Technical Geodetics */}
      <svg
        className="absolute inset-0 w-full h-full opacity-25"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 1920 1080"
        preserveAspectRatio="xMidYMid slice"
      >
        {/* Top-Right Highland Iso-curves */}
        <g stroke="#38bdf8" fill="none" opacity="0.6">
          <path
            d="M1350,-50 C1420,120 1590,190 1740,160 C1860,130 1940,60 2000,-40"
            strokeWidth="0.8"
          />
          <path
            d="M1410,-50 C1470,90 1620,150 1760,120 C1870,100 1950,30 2000,-50"
            strokeWidth="1.2"
          />
          <path
            d="M1470,-50 C1520,60 1650,110 1780,85 C1870,70 1930,10 1980,-50"
            strokeWidth="0.8"
          />
          <path
            d="M1540,-50 C1580,30 1680,75 1800,55 C1870,40 1910,-10 1950,-50"
            strokeWidth="1.5"
          />
        </g>

        {/* Bottom-Left Ridge Formations */}
        <g stroke="#94a3b8" fill="none" opacity="0.45">
          <path
            d="M-80,680 C120,670 260,780 410,790 C560,800 700,720 890,750 C1060,780 1200,900 1340,940"
            strokeWidth="0.8"
          />
          <path
            d="M-80,740 C140,730 290,830 450,840 C600,850 740,770 930,800 C1100,830 1240,950 1370,990"
            strokeWidth="1.2"
          />
          <path
            d="M-80,810 C160,800 320,890 490,900 C640,910 780,830 970,860 C1140,890 1280,1000 1400,1040"
            strokeWidth="0.8"
          />
          <path
            d="M-80,890 C180,880 350,960 530,970 C680,980 820,900 1010,930 C1180,960 1320,1050 1430,1100"
            strokeWidth="1.4"
          />
        </g>

        {/* Technical Coordinate & Elevation Notations (Engineering Geodetics) */}
        <g
          className="font-mono text-[9px] select-none"
          fill="#64748b"
          opacity="0.4"
          letterSpacing="0.1em"
        >
          {/* Topographic elevation labels */}
          <text x="1420" y="80">ELEV +480M // LAT 41.83°</text>
          <text x="1630" y="145">CONTOUR 08 // Δ 25M</text>
          <text x="280" y="775">RIDGE FLANK [WEST // 320M]</text>
          <text x="730" y="790">BASE CONTOUR // 04</text>
          <text x="1150" y="910">SURFACE REF [0.82-SIGMA]</text>

          {/* Technical Geodetic Cross-hairs */}
          <path d="M1410,77 L1430,77 M1420,67 L1420,87" stroke="#38bdf8" strokeWidth="0.75" />
          <path d="M270,772 L290,772 M280,762 L280,782" stroke="#64748b" strokeWidth="0.75" />
          <path d="M1140,907 L1160,907 M1150,897 L1150,917" stroke="#38bdf8" strokeWidth="0.75" />
          <path d="M1750,220 L1770,220 M1760,210 L1760,230" stroke="#64748b" strokeWidth="0.75" />
        </g>
      </svg>

      {/* 5. Subdued Precision Micro-Dot Matrix Overlay */}
      <svg
        className="absolute inset-0 w-full h-full opacity-[0.035]"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <pattern id="topoDotGrid" width="32" height="32" patternUnits="userSpaceOnUse">
            <circle cx="2" cy="2" r="1" fill="#cbd5e1" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#topoDotGrid)" />
      </svg>

      {/* 6. Subtle Directional Topographic Lighting Gradient */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'linear-gradient(135deg, rgba(56, 189, 248, 0.03) 0%, transparent 40%, rgba(15, 23, 42, 0.3) 100%)',
        }}
      />

      {/* 7. Central Contrast Vignette Mask (Keeps center dark & crisp for code/text legibility) */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(circle at 50% 35%, rgba(7, 9, 14, 0.45) 0%, rgba(7, 9, 14, 0.8) 65%, #07090e 95%)',
        }}
      />
    </div>
  );
});

TopographicBackground.displayName = 'TopographicBackground';
