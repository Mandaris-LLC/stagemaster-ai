import React, { useState, useRef } from 'react';
import { Maximize2, MoveHorizontal } from 'lucide-react';

const BeforeAfterSlider = ({ original, staged }) => {
    const [sliderPos, setSliderPos] = useState(50);
    const containerRef = useRef(null);

    const handleMove = (e) => {
        if (!containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        const x = (e.clientX || (e.touches && e.touches[0].clientX));
        if (x === undefined) return;

        let position = ((x - rect.left) / rect.width) * 100;
        if (position < 0) position = 0;
        if (position > 100) position = 100;
        setSliderPos(position);
    };

    return (
        <div
            ref={containerRef}
            className="relative w-full min-h-[200px] overflow-hidden rounded-2xl cursor-col-resize select-none shadow-elevation-4 border border-outline-variant bg-surface-container"
            onMouseMove={handleMove}
            onTouchMove={handleMove}
        >
            {/* Background: Staged */}
            <img
                src={staged}
                alt="Staged"
                className="w-full h-auto block"
            />

            {/* Foreground: Original (Clipped) */}
            <div
                className="absolute inset-0 w-full h-full overflow-hidden"
                style={{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)` }}
            >
                <img
                    src={original}
                    alt="Original"
                    className="w-full h-auto block"
                />

                {/* Compliance Label */}
                <div className="absolute bottom-4 left-4 z-30">
                    <div className="bg-primary/80 backdrop-blur-sm px-3 py-1.5 rounded-lg">
                        <p className="text-xs text-white font-medium">
                            Virtually Staged
                        </p>
                    </div>
                </div>
            </div>

            {/* Slider Line & Handle */}
            <div
                className="absolute top-0 bottom-0 w-0.5 bg-white z-40"
                style={{ left: `${sliderPos}%` }}
            >
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-10 h-10 bg-white rounded-full shadow-elevation-4 flex items-center justify-center border-2 border-accent cursor-grab active:cursor-grabbing hover:scale-110 transition-transform">
                    <MoveHorizontal size={18} className="text-accent" />
                </div>
            </div>

            {/* Labels */}
            <div className="absolute top-4 left-4 z-20 pointer-events-none">
                <div className="bg-primary/70 backdrop-blur-sm px-3 py-1.5 rounded-lg">
                    <span className="text-xs font-medium text-white">Original</span>
                </div>
            </div>

            <div className="absolute top-4 right-4 z-20 pointer-events-none">
                <div className="bg-accent/90 backdrop-blur-sm px-3 py-1.5 rounded-lg">
                    <span className="text-xs font-medium text-white">AI Staged</span>
                </div>
            </div>

            {/* Fullscreen Button */}
            <button className="absolute bottom-4 right-4 z-30 bg-white/90 hover:bg-white p-2 rounded-lg shadow-elevation-2 text-primary transition-all hover:scale-105">
                <Maximize2 size={16} />
            </button>
        </div>
    );
};

export default BeforeAfterSlider;
