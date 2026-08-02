import React, { useEffect, useRef } from 'react';
import Card from '../common/Card';
import { Activity } from 'lucide-react';

export const ChartPlaceholder = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;
    let resizeObserver;
    
    // Function to calculate dimensions
    const resizeCanvas = () => {
      canvas.width = canvas.parentElement.clientWidth * 2;
      canvas.height = 200;
    };
    
    resizeCanvas();

    // Watch for size changes to keep it responsive
    if (window.ResizeObserver) {
      resizeObserver = new ResizeObserver(() => {
        resizeCanvas();
      });
      resizeObserver.observe(canvas.parentElement);
    }
    
    let x = 0;
    const points = [];
    
    // Draw grid lines
    const drawGrid = (c, w, h) => {
      c.strokeStyle = 'rgba(16, 185, 129, 0.05)';
      c.lineWidth = 1;
      
      // Vertical grid
      for (let i = 0; i < w; i += 20) {
        c.beginPath();
        c.moveTo(i, 0);
        c.lineTo(i, h);
        c.stroke();
      }
      
      // Horizontal grid
      for (let j = 0; j < h; j += 20) {
        c.beginPath();
        c.moveTo(0, j);
        c.lineTo(w, j);
        c.stroke();
      }
    };

    // Calculate Y for ECG oscilloscope waveform
    const getECGValue = (tick, h) => {
      const cycle = tick % 90; // Heartbeat interval cycles
      const baseline = h / 2;
      
      if (cycle < 10) return baseline;
      if (cycle >= 10 && cycle < 18) {
        // P-wave
        const angle = ((cycle - 10) / 8) * Math.PI;
        return baseline - Math.sin(angle) * 7;
      }
      if (cycle >= 18 && cycle < 22) return baseline;
      if (cycle >= 22 && cycle < 24) {
        // Q-wave
        return baseline + 4;
      }
      if (cycle >= 24 && cycle < 28) {
        // R-spike
        const progress = (cycle - 24) / 4;
        return baseline - 55 * progress;
      }
      if (cycle >= 28 && cycle < 31) {
        // S-dip
        const progress = (cycle - 28) / 3;
        return baseline - 55 + 75 * progress;
      }
      if (cycle >= 31 && cycle < 34) {
        // Recovery
        const progress = (cycle - 31) / 3;
        return baseline + 20 - 20 * progress;
      }
      if (cycle >= 34 && cycle < 42) return baseline;
      if (cycle >= 42 && cycle < 55) {
        // T-wave
        const angle = ((cycle - 42) / 13) * Math.PI;
        return baseline - Math.sin(angle) * 12;
      }
      return baseline;
    };

    let tick = 0;

    const render = () => {
      const w = canvas.width;
      const h = canvas.height;
      
      // Oscilloscope persistent screen phosphor fading tail effect
      ctx.fillStyle = 'rgba(15, 23, 42, 0.12)';
      ctx.fillRect(0, 0, w, h);
      
      drawGrid(ctx, w, h);
      
      // Sweep indicator coordinates
      x = (x + 3.2) % w;
      
      const y = getECGValue(tick, h);
      points[Math.floor(x)] = y;
      
      ctx.strokeStyle = '#10B981'; // Green sweep wave
      ctx.lineWidth = 2.5;
      ctx.shadowBlur = 8;
      ctx.shadowColor = '#10B981';
      ctx.beginPath();
      
      let drawing = false;
      for (let i = 0; i < w; i++) {
        const val = points[i];
        if (val !== undefined) {
          // Erase segment just ahead of sweep point
          if (Math.abs(i - x) < 30) {
            drawing = false;
            continue;
          }
          
          if (!drawing) {
            ctx.moveTo(i, val);
            drawing = true;
          } else {
            ctx.lineTo(i, val);
          }
        }
      }
      ctx.stroke();
      
      // Sweep point head glow
      ctx.fillStyle = '#34D399';
      ctx.shadowBlur = 12;
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, 2 * Math.PI);
      ctx.fill();
      
      ctx.shadowBlur = 0;
      tick++;
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      if (resizeObserver) resizeObserver.disconnect();
    };
  }, []);

  return (
    <Card 
      title="Live Attending Telemetry Monitor" 
      subtitle="MAX30102 Diagnostic Output - 60Hz Cardiac ECG Stream"
      actions={
        <div className="flex items-center gap-1.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-0.5 rounded-full text-xs font-bold animate-pulse select-none">
          <Activity className="w-3.5 h-3.5" />
          <span>Biometric Stream Live</span>
        </div>
      }
      className="col-span-1 lg:col-span-3 overflow-hidden bg-slate-950 border-slate-800"
    >
      <div className="w-full relative mt-4 overflow-hidden rounded-xl bg-slate-950 p-1 border border-slate-850">
        <canvas ref={canvasRef} className="w-full block h-[200px]" />
        
        {/* ECG overlay metrics values */}
        <div className="absolute top-4 right-4 flex gap-3.5 select-none pointer-events-none">
          <div className="bg-slate-900/90 border border-white/5 rounded-lg p-2 backdrop-blur text-right">
            <span className="text-[8px] text-slate-400 font-black block uppercase tracking-wider">Heart Rate</span>
            <span className="text-xs font-black text-emerald-400 font-mono">72 BPM</span>
          </div>
          <div className="bg-slate-900/90 border border-white/5 rounded-lg p-2 backdrop-blur text-right">
            <span className="text-[8px] text-slate-400 font-black block uppercase tracking-wider">SpO₂ Vitals</span>
            <span className="text-xs font-black text-blue-400 font-mono">98%</span>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default ChartPlaceholder;
