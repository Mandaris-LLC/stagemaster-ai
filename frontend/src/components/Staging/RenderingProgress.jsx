import React from 'react';
import { motion } from 'framer-motion';
import { Loader2, Zap, Clock, Compass } from 'lucide-react';

const RenderingProgress = ({ job }) => {
    if (!job) return null;

    return (
        <div className="w-full bg-surface border border-outline-variant rounded-2xl p-8 shadow-elevation-3">
            {/* Header */}
            <div className="flex justify-between items-start mb-8">
                <div className="space-y-2">
                    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent-50 text-accent-700 border border-accent-200">
                        <Loader2 size={14} className="animate-spin" />
                        <span className="text-xs font-semibold">Processing</span>
                    </div>
                    <h2 className="text-2xl font-semibold text-primary">
                        Generating Staged Image
                    </h2>
                    <p className="text-on-surface-variant">
                        <span className="capitalize">{job.room_type}</span> • <span className="capitalize">{job.style_preset}</span> Style
                    </p>
                </div>
                <div className="text-right">
                    <span className="text-4xl font-bold text-accent tabular-nums">
                        {Math.round(job.progress_percent)}%
                    </span>
                </div>
            </div>

            {/* Progress Bar */}
            <div className="relative mb-8">
                <div className="w-full h-2 bg-surface-container-high rounded-full overflow-hidden">
                    <motion.div
                        className="h-full bg-accent rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${job.progress_percent}%` }}
                        transition={{ duration: 0.5, ease: "easeOut" }}
                    />
                </div>
            </div>

            {/* Status Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6 border-t border-outline-variant">
                <div className="flex items-start gap-3">
                    <div className="p-2.5 bg-info/10 rounded-lg text-info">
                        <Compass size={18} />
                    </div>
                    <div>
                        <p className="text-xs font-medium text-on-surface-muted uppercase tracking-wide mb-1">Current Step</p>
                        <p className="text-sm font-medium text-primary">{job.current_step || 'Analyzing layout...'}</p>
                    </div>
                </div>

                <div className="flex items-start gap-3">
                    <div className="p-2.5 bg-warning/10 rounded-lg text-warning">
                        <Clock size={18} />
                    </div>
                    <div>
                        <p className="text-xs font-medium text-on-surface-muted uppercase tracking-wide mb-1">Elapsed Time</p>
                        <p className="text-sm font-medium text-primary tabular-nums">00:45</p>
                    </div>
                </div>

                <div className="flex items-start gap-3">
                    <div className="p-2.5 bg-success/10 rounded-lg text-success">
                        <Zap size={18} />
                    </div>
                    <div>
                        <p className="text-xs font-medium text-on-surface-muted uppercase tracking-wide mb-1">Est. Remaining</p>
                        <p className="text-sm font-medium text-primary tabular-nums">~01:45</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RenderingProgress;
