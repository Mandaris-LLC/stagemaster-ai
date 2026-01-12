import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap } from 'lucide-react';
import Header from '../components/Common/Header';
import PhotoDropzone from '../components/Upload/PhotoDropzone';
import RoomTypeSelector from '../components/Staging/RoomTypeSelector';
import StylePresets from '../components/Staging/StylePresets';
import { uploadImage, createStagingJob } from '../services/api';
import heroImage from '../assets/hero-room.png';

const LandingPage = () => {
    const navigate = useNavigate();
    const [file, setFile] = useState(null);
    const [roomType, setRoomType] = useState('living_room');
    const [style, setStyle] = useState('modern');
    const [fixWhiteBalance, setFixWhiteBalance] = useState(true);
    const [wallDecorations, setWallDecorations] = useState(true);
    const [includeTV, setIncludeTV] = useState(false);
    const [isUploading, setIsUploading] = useState(false);

    const isTVDisabled = roomType === 'bathroom' || roomType === 'kitchen';

    const handleStartStaging = async () => {
        if (!file) return;

        setIsUploading(true);
        try {
            const imageData = await uploadImage(file);
            const jobData = await createStagingJob(imageData.id, roomType, style, {
                fixWhiteBalance,
                wallDecorations,
                includeTV: !isTVDisabled && includeTV
            });
            navigate(`/job/${jobData.id}`);
        } catch (error) {
            console.error("Staging failed:", error);
            alert("Failed to start staging. Please try again.");
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="min-h-screen bg-surface-dim">
            <Header />

            <main className="max-w-6xl mx-auto px-6 py-8">
                {/* Hero Section - Side by Side */}
                <div className="flex flex-col lg:flex-row items-center gap-8 mb-6 w-full">
                    {/* Left: Text Content */}
                    <div className="flex-1 text-left">
                        <h1 className="text-5xl md:text-6xl font-bold mb-4 text-primary leading-tight font-display">
                            Clean & Professional
                        </h1>
                        <p className="text-on-surface-variant text-xl mb-8 max-w-lg">
                            Transform empty rooms into stunning staged spaces.
                        </p>
                        <button
                            onClick={() => document.getElementById('main-card').scrollIntoView({ behavior: 'smooth' })}
                            className="bg-accent hover:bg-accent-700 px-6 py-3 rounded-lg text-white font-semibold shadow-elevation-2 hover:shadow-elevation-3 transition-all active:scale-[0.98]"
                        >
                            Start Staging
                        </button>
                    </div>

                    {/* Right: Hero Image */}
                    <div className="flex-1">
                        <img
                            src={heroImage}
                            alt="Staged living room"
                            className="w-full rounded-2xl shadow-elevation-3 object-cover"
                        />
                    </div>
                </div>

                {/* Main Card - Improved Step-by-Step Layout */}
                <div id="main-card" className="bg-surface rounded-3xl shadow-elevation-4 border border-outline-variant overflow-hidden">
                    <div className="grid lg:grid-cols-12 gap-0">
                        {/* Left: Upload Section (Step 1) */}
                        <div className="lg:col-span-5 p-8 border-b lg:border-b-0 lg:border-r border-outline-variant bg-surface-container-low">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-bold text-sm">1</div>
                                <h3 className="text-xl font-bold text-primary">Upload Room</h3>
                            </div>
                            <PhotoDropzone
                                onFileSelect={setFile}
                                selectedFile={file}
                                onClear={() => setFile(null)}
                            />
                            <p className="mt-4 text-sm text-on-surface-variant">
                                Tip: Use a clear, well-lit photo of an empty or sparsely furnished room for best results.
                            </p>
                        </div>

                        {/* Right: Configuration Section (Step 2) */}
                        <div className="lg:col-span-7 p-8 space-y-8">
                            <div className="flex items-center gap-3 mb-2">
                                <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-bold text-sm">2</div>
                                <h3 className="text-xl font-bold text-primary">Configure Staging</h3>
                            </div>

                            <div className="grid md:grid-cols-2 gap-8">
                                {/* Room Type */}
                                <div>
                                    <h4 className="text-sm font-bold text-on-surface-variant uppercase tracking-wider mb-4">Room Type</h4>
                                    <RoomTypeSelector selected={roomType} onSelect={setRoomType} />
                                </div>

                                {/* Design Styles */}
                                <div>
                                    <h4 className="text-sm font-bold text-on-surface-variant uppercase tracking-wider mb-4">Design Style</h4>
                                    <StylePresets selected={style} onSelect={setStyle} />
                                </div>
                            </div>

                            {/* Additional Options */}
                            <div className="pt-4 border-t border-outline-variant">
                                <h4 className="text-sm font-bold text-on-surface-variant uppercase tracking-wider mb-4">Enhancements</h4>
                                <div className="flex flex-wrap gap-6">
                                    <label className="flex items-center gap-3 cursor-pointer group">
                                        <div className="relative flex items-center">
                                            <input
                                                type="checkbox"
                                                checked={fixWhiteBalance}
                                                onChange={(e) => setFixWhiteBalance(e.target.checked)}
                                                className="peer sr-only"
                                            />
                                            <div className="w-5 h-5 border-2 border-outline rounded peer-checked:bg-primary peer-checked:border-primary transition-all" />
                                            <svg className="absolute w-3.5 h-3.5 text-white left-[3px] opacity-0 peer-checked:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="4">
                                                <path d="M5 13l4 4L19 7" />
                                            </svg>
                                        </div>
                                        <span className="text-on-surface font-medium group-hover:text-primary transition-colors">Fix White Balance</span>
                                    </label>

                                    <label className="flex items-center gap-3 cursor-pointer group">
                                        <div className="relative flex items-center">
                                            <input
                                                type="checkbox"
                                                checked={wallDecorations}
                                                onChange={(e) => setWallDecorations(e.target.checked)}
                                                className="peer sr-only"
                                            />
                                            <div className="w-5 h-5 border-2 border-outline rounded peer-checked:bg-primary peer-checked:border-primary transition-all" />
                                            <svg className="absolute w-3.5 h-3.5 text-white left-[3px] opacity-0 peer-checked:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="4">
                                                <path d="M5 13l4 4L19 7" />
                                            </svg>
                                        </div>
                                        <span className="text-on-surface font-medium group-hover:text-primary transition-colors">Wall Decorations</span>
                                    </label>

                                    <label className={`flex items-center gap-3 group ${isTVDisabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}>
                                        <div className="relative flex items-center">
                                            <input
                                                type="checkbox"
                                                checked={!isTVDisabled && includeTV}
                                                onChange={(e) => setIncludeTV(e.target.checked)}
                                                disabled={isTVDisabled}
                                                className="peer sr-only"
                                            />
                                            <div className={`w-5 h-5 border-2 rounded transition-all ${isTVDisabled ? 'border-outline-variant bg-surface-container' : 'border-outline peer-checked:bg-primary peer-checked:border-primary'}`} />
                                            <svg className="absolute w-3.5 h-3.5 text-white left-[3px] opacity-0 peer-checked:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="4">
                                                <path d="M5 13l4 4L19 7" />
                                            </svg>
                                        </div>
                                        <span className={`font-medium transition-colors ${isTVDisabled ? 'text-on-surface-variant' : 'text-on-surface group-hover:text-primary'}`}>Include TV</span>
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Bottom: Action Bar (Step 3) */}
                    <div className="bg-surface-container-high p-6 border-t border-outline-variant flex flex-col md:flex-row items-center justify-between gap-6">
                        <div className="flex-1">
                            <h4 className="font-bold text-primary flex items-center gap-2">
                                <div className="w-6 h-6 rounded-full bg-primary text-white flex items-center justify-center font-bold text-xs">3</div>
                                Ready to transform?
                            </h4>
                            <p className="text-sm text-on-surface-variant">
                                {!file
                                    ? "Please upload a photo to begin the magic."
                                    : `Staging your ${roomType.replace('_', ' ')} in ${style} style.`}
                            </p>
                        </div>
                        
                        <button
                            onClick={() => {
                                if (!file) {
                                    document.getElementById('main-card').scrollIntoView({ behavior: 'smooth' });
                                } else {
                                    handleStartStaging();
                                }
                            }}
                            disabled={isUploading}
                            className={`
                                min-w-[240px] py-4 px-8 rounded-2xl font-bold text-lg flex items-center justify-center gap-3 transition-all duration-300
                                ${!file
                                    ? 'bg-white text-primary border-2 border-primary/20 hover:border-primary/40 hover:bg-primary/5'
                                    : 'bg-accent text-white shadow-elevation-3 hover:shadow-elevation-4 hover:scale-[1.02] active:scale-[0.98]'}
                                ${isUploading ? 'animate-pulse opacity-70 cursor-wait' : ''}
                            `}
                        >
                            {isUploading ? (
                                <>
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                    Processing...
                                </>
                            ) : (
                                <>
                                    <Zap size={22} className={file ? 'fill-white' : 'text-primary/40'} />
                                    {file ? 'Start Staging Magic' : 'Upload Photo First'}
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default LandingPage;
