import React, { useState, useRef } from 'react';
import { ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';
import { GlassCard } from '../glass/GlassCard';
import type { BoundingBox } from '../../types';

interface ForensicImageViewerProps {
  originalUrl: string;
  heatmapUrl: string;
  activeBbox?: BoundingBox | null;
  onSelectRegion?: (bbox: BoundingBox) => void;
}

export const ForensicImageViewer: React.FC<ForensicImageViewerProps> = ({
  originalUrl,
  heatmapUrl,
  activeBbox,
}) => {
  const [zoomLevel, setZoomLevel] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [startPan, setStartPan] = useState({ x: 0, y: 0 });
  const [viewMode, setViewMode] = useState<'split' | 'heatmap' | 'original' | 'overlay'>('split');
  const [overlayOpacity, setOverlayOpacity] = useState(0.5);

  const containerRef = useRef<HTMLDivElement>(null);

  const handleZoom = (delta: number) => {
    setZoomLevel((prev) => Math.min(4, Math.max(0.5, Number((prev + delta).toFixed(1)))));
  };

  const handleReset = () => {
    setZoomLevel(1);
    setPan({ x: 0, y: 0 });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsPanning(true);
    setStartPan({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isPanning) return;
    setPan({
      x: e.clientX - startPan.x,
      y: e.clientY - startPan.y,
    });
  };

  const handleMouseUp = () => {
    setIsPanning(false);
  };

  return (
    <GlassCard className="p-4 space-y-3">
      {/* Viewer Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs border-b border-slate-200 pb-2.5">
        <div className="flex items-center gap-1.5 bg-slate-100 p-0.5 rounded-lg border border-slate-200">
          <button
            type="button"
            onClick={() => setViewMode('split')}
            className={`px-2.5 py-1 rounded-md font-medium transition ${
              viewMode === 'split' ? 'bg-white text-blue-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Side-by-Side
          </button>
          <button
            type="button"
            onClick={() => setViewMode('heatmap')}
            className={`px-2.5 py-1 rounded-md font-medium transition ${
              viewMode === 'heatmap' ? 'bg-white text-blue-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            ELA Heatmap
          </button>
          <button
            type="button"
            onClick={() => setViewMode('original')}
            className={`px-2.5 py-1 rounded-md font-medium transition ${
              viewMode === 'original' ? 'bg-white text-blue-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Evidence Original
          </button>
          <button
            type="button"
            onClick={() => setViewMode('overlay')}
            className={`px-2.5 py-1 rounded-md font-medium transition ${
              viewMode === 'overlay' ? 'bg-white text-blue-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Alpha Blend
          </button>
        </div>

        {viewMode === 'overlay' && (
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-slate-500 font-mono">Heatmap Alpha:</span>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={overlayOpacity}
              onChange={(e) => setOverlayOpacity(parseFloat(e.target.value))}
              className="w-24 h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer"
            />
            <span className="text-[11px] font-mono text-slate-700">{(overlayOpacity * 100).toFixed(0)}%</span>
          </div>
        )}

        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => handleZoom(0.25)}
            className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 transition"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={() => handleZoom(-0.25)}
            className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 transition"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={handleReset}
            className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 transition"
            title="Reset View"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
          <span className="text-[11px] font-mono text-slate-500 ml-1.5">
            {(zoomLevel * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Main Viewport */}
      <div
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className="relative rounded-xl border border-slate-300 bg-slate-950 overflow-hidden min-h-[460px] cursor-grab active:cursor-grabbing select-none flex items-center justify-center p-2"
      >
        <div
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoomLevel})`,
            transformOrigin: 'center center',
            transition: isPanning ? 'none' : 'transform 0.15s ease-out',
          }}
          className="relative max-w-full"
        >
          {viewMode === 'split' ? (
            <div className="flex gap-4 items-center">
              <div className="relative border border-slate-800 rounded overflow-hidden shadow-xl">
                <img
                  src={originalUrl}
                  alt="Original Document"
                  className="max-h-[420px] w-auto object-contain block"
                  draggable={false}
                />
                <span className="absolute bottom-2 left-2 bg-black/75 px-2 py-0.5 rounded text-[10px] font-mono text-white">
                  ORIGINAL EVIDENCE
                </span>
              </div>
              <div className="relative border border-slate-800 rounded overflow-hidden shadow-xl">
                <img
                  src={heatmapUrl}
                  alt="ELA Heatmap"
                  className="max-h-[420px] w-auto object-contain block"
                  draggable={false}
                />
                <span className="absolute bottom-2 left-2 bg-black/75 px-2 py-0.5 rounded text-[10px] font-mono text-white">
                  ELA ERROR HEATMAP (Q95)
                </span>
              </div>
            </div>
          ) : viewMode === 'heatmap' ? (
            <div className="relative border border-slate-800 rounded overflow-hidden shadow-xl">
              <img
                src={heatmapUrl}
                alt="ELA Heatmap"
                className="max-h-[440px] w-auto object-contain block"
                draggable={false}
              />
              <span className="absolute bottom-2 left-2 bg-black/75 px-2 py-0.5 rounded text-[10px] font-mono text-white">
                ERROR LEVEL ANALYSIS (JET COLORMAP)
              </span>
            </div>
          ) : viewMode === 'original' ? (
            <div className="relative border border-slate-800 rounded overflow-hidden shadow-xl">
              <img
                src={originalUrl}
                alt="Original Evidence"
                className="max-h-[440px] w-auto object-contain block"
                draggable={false}
              />
              <span className="absolute bottom-2 left-2 bg-black/75 px-2 py-0.5 rounded text-[10px] font-mono text-white">
                ORIGINAL TAMPER-EVIDENT SCAN
              </span>
            </div>
          ) : (
            /* Alpha Blend Overlay */
            <div className="relative border border-slate-800 rounded overflow-hidden shadow-xl">
              <img
                src={originalUrl}
                alt="Original Base"
                className="max-h-[440px] w-auto object-contain block"
                draggable={false}
              />
              <img
                src={heatmapUrl}
                alt="Heatmap Layer"
                style={{ opacity: overlayOpacity }}
                className="absolute inset-0 w-full h-full object-contain pointer-events-none"
                draggable={false}
              />
              <span className="absolute bottom-2 left-2 bg-black/75 px-2 py-0.5 rounded text-[10px] font-mono text-white">
                ALPHA COMPOSITE ({(overlayOpacity * 100).toFixed(0)}%)
              </span>
            </div>
          )}

          {/* Highlight Suspect Region Box if provided */}
          {activeBbox && activeBbox.w > 0 && (
            <div
              style={{
                left: `${activeBbox.x}px`,
                top: `${activeBbox.y}px`,
                width: `${activeBbox.w}px`,
                height: `${activeBbox.h}px`,
              }}
              className="absolute border-2 border-red-500 bg-red-500/20 rounded pointer-events-none animate-pulse"
            />
          )}
        </div>
      </div>

      {/* Heatmap Legend */}
      <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-500 pt-1">
        <div className="flex items-center gap-2">
          <span>Heatmap Color Scale:</span>
          <div className="h-2.5 w-36 rounded-full bg-gradient-to-r from-blue-700 via-green-500 via-yellow-400 to-red-600 border border-slate-300" />
          <span className="font-mono text-[10px]">Low (0) → Extreme Variance (255)</span>
        </div>
        <span>Pan: Click & drag • Zoom: Controls or pinch</span>
      </div>
    </GlassCard>
  );
};
