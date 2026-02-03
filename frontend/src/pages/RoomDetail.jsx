import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
    ArrowLeft,
    Upload,
    Image as ImageIcon,
    CheckCircle2,
    Play,
    Loader2,
    Info,
    Layers,
    Camera,
    Sparkles,
    X,
    Zap,
    Trash2,
    AlertTriangle,
    Plus
} from 'lucide-react';
import { getRoom, uploadImage, createStagingJob, deleteImage, deleteRoom } from '../services/api';
import Header from '../components/Common/Header';
import StylePresets from '../components/Staging/StylePresets';

const RoomDetail = () => {
    const { roomId } = useParams();
    const navigate = useNavigate();
    const [room, setRoom] = useState(null);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [startingJob, setStartingJob] = useState(null);
    const [deleting, setDeleting] = useState(null); // 'room' or imageId

    // UI State
    const [showStaged, setShowStaged] = useState({}); // imageId -> boolean

    // Staging Options State
    const [selectedImage, setSelectedImage] = useState(null);
    const [style, setStyle] = useState('modern');
    const [fixWhiteBalance, setFixWhiteBalance] = useState(false);
    const [wallDecorations, setWallDecorations] = useState(true);
    const [includeTV, setIncludeTV] = useState(false);

    useEffect(() => {
        fetchRoomData();
    }, [roomId]);

    const fetchRoomData = async () => {
        try {
            const data = await getRoom(roomId);
            setRoom(data);

            // Initialize showStaged for any new images with results
            if (data.images) {
                const initialShowStaged = {};
                data.images.forEach(img => {
                    if (img.latest_result_url) {
                        initialShowStaged[img.id] = true;
                    }
                });
                setShowStaged(prev => ({ ...initialShowStaged, ...prev }));
            }
        } catch (error) {
            console.error("Error fetching room:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        setUploading(true);
        const isFirstImage = !room.images || room.images.length === 0;
        try {
            const newImage = await uploadImage(file, roomId);
            await fetchRoomData();
            if (isFirstImage) {
                // Automatically open options for the first image
                handleOpenOptions(newImage);
            }
        } catch (error) {
            console.error("Error uploading image:", error);
            alert("Failed to upload image. Please try again.");
        } finally {
            setUploading(false);
        }
    };

    const handleOpenOptions = (image) => {
        setSelectedImage(image);

        // If it's NOT the reference image, try to inherit settings from the reference image
        if (image.id !== room.reference_image_id) {
            const referenceImage = room.images?.find(img => img.id === room.reference_image_id);
            if (referenceImage && referenceImage.latest_settings) {
                const s = referenceImage.latest_settings;
                setStyle(s.style_preset || 'modern');
                setFixWhiteBalance(s.fix_white_balance || false);
                setWallDecorations(s.wall_decorations !== undefined ? s.wall_decorations : true);
                setIncludeTV(s.include_tv || false);
            }
        } else if (image.latest_settings) {
            // If it IS the reference image, use its own latest settings as default
            const s = image.latest_settings;
            setStyle(s.style_preset || 'modern');
            setFixWhiteBalance(s.fix_white_balance || false);
            setWallDecorations(s.wall_decorations !== undefined ? s.wall_decorations : true);
            setIncludeTV(s.include_tv || false);
        }
    };

    const handleStartStaging = async () => {
        if (!selectedImage) return;

        setStartingJob(selectedImage.id);
        try {
            const job = await createStagingJob(selectedImage.id, room.room_type, style, {
                roomId: roomId,
                fixWhiteBalance,
                wallDecorations,
                includeTV
            });
            navigate(`/job/${job.id}`, { state: { from: 'room', roomId: roomId } });
        } catch (error) {
            console.error("Error starting job:", error);
            alert("Failed to start staging job.");
        } finally {
            setStartingJob(null);
            setSelectedImage(null);
        }
    };

    const toggleStaged = (imageId) => {
        setShowStaged(prev => ({
            ...prev,
            [imageId]: !prev[imageId]
        }));
    };

    const handleDeleteImage = async (imageId) => {
        console.log("handleDeleteImage clicked", imageId);
        if (!window.confirm("Are you sure you want to delete this image? This action cannot be undone.")) return;

        console.log("handleDeleteImage confirmed, starting deletion...");
        setDeleting(imageId);
        try {
            await deleteImage(imageId);
            console.log("handleDeleteImage success, refreshing data...");
            fetchRoomData();
        } catch (error) {
            console.error("Error deleting image:", error);
            alert("Failed to delete image: " + (error.response?.data?.detail || error.message));
        } finally {
            setDeleting(null);
        }
    };

    const handleDeleteRoom = async () => {
        console.log("handleDeleteRoom clicked", room);
        if (room.images && room.images.length > 0) {
            alert("You must delete all images before you can delete the room.");
            return;
        }

        if (!window.confirm("Are you sure you want to delete this empty room?")) return;

        console.log("handleDeleteRoom confirmed, starting deletion...");
        setDeleting('room');
        try {
            await deleteRoom(roomId);
            console.log("handleDeleteRoom success, navigating back...");
            navigate(`/property/${room.property_id}`);
        } catch (error) {
            console.error("Error deleting room:", error);
            alert("Failed to delete room: " + (error.response?.data?.detail || error.message));
        } finally {
            setDeleting(null);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-surface-dim">
                <Header />
                <div className="flex flex-col items-center justify-center py-40">
                    <Loader2 className="animate-spin text-accent mb-4" size={40} />
                    <p className="text-on-surface-variant font-medium">Loading room details...</p>
                </div>
            </div>
        );
    }

    if (!room) {
        return (
            <div className="min-h-screen bg-surface-dim">
                <Header />
                <div className="max-w-7xl mx-auto px-6 py-12 text-center">
                    <h1 className="text-3xl font-display font-bold text-primary mb-4">Room not found</h1>
                    <Link to="/properties" className="text-accent font-semibold flex items-center justify-center gap-2">
                        <ArrowLeft size={20} />
                        Back to Properties
                    </Link>
                </div>
            </div>
        );
    }

    const referenceImage = room.images?.find(img => img.id === room.reference_image_id);
    const otherImages = room.images?.filter(img => img.id !== room.reference_image_id) || [];
    const isTVDisabled = room.room_type === 'bathroom' || room.room_type === 'kitchen';
    const isSecondaryAngle = selectedImage && selectedImage.id !== room.reference_image_id;

    return (
        <div className="min-h-screen bg-surface-dim">
            <Header />
            <main className="max-w-7xl mx-auto px-6 py-12">
                <div className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
                    <div>
                        <button
                            onClick={() => navigate(-1)}
                            className="text-on-surface-variant hover:text-primary flex items-center gap-2 text-sm font-medium mb-4 transition-colors"
                        >
                            <ArrowLeft size={16} />
                            Back
                        </button>
                        <h1 className="text-4xl font-display font-bold text-primary mb-2">{room.name}</h1>
                        <div className="flex items-center gap-3">
                            <span className="bg-primary/5 text-primary text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">
                                {room.room_type}
                            </span>
                            <span className="text-on-surface-variant text-sm flex items-center gap-1">
                                <ImageIcon size={14} />
                                {room.images?.length || 0} Images
                            </span>
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <button
                            onClick={handleDeleteRoom}
                            disabled={deleting === 'room'}
                            className="flex items-center gap-2 px-4 py-3 rounded-xl font-semibold text-error hover:bg-error/10 transition-colors disabled:opacity-50"
                        >
                            {deleting === 'room' ? <Loader2 size={18} className="animate-spin" /> : <Trash2 size={18} />}
                            Delete Room
                        </button>
                        <label className={`
                            flex items-center gap-2 px-6 py-3 rounded-xl font-semibold cursor-pointer shadow-elevation-2 transition-all active:scale-[0.98]
                            ${uploading ? 'bg-surface-container text-on-surface-muted cursor-not-allowed' : 'bg-primary text-white hover:bg-primary-700'}
                        `}>
                            {uploading ? (
                                <Loader2 size={20} className="animate-spin" />
                            ) : (
                                <Upload size={20} />
                            )}
                            {uploading ? 'Uploading...' : 'Upload New Angle'}
                            <input type="file" className="hidden" onChange={handleFileUpload} disabled={uploading} accept="image/*" />
                        </label>
                    </div>
                </div>

                {/* Empty State or Reference Image Section */}
                {!referenceImage ? (
                    <div className="bg-white rounded-3xl p-20 text-center border-2 border-dashed border-outline-variant animate-fade-in">
                        <div className="bg-accent-50 w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-8 text-accent">
                            <Camera size={40} />
                        </div>
                        <h2 className="text-3xl font-display font-bold text-primary mb-4">Start Staging this Room</h2>
                        <p className="text-on-surface-variant max-w-lg mx-auto mb-10 text-lg">
                            Upload your first photo of the {room.room_type}. This will become your reference view for all other angles.
                        </p>
                        <label className="bg-accent hover:bg-accent-700 text-white px-10 py-4 rounded-2xl font-bold text-lg inline-flex items-center gap-3 shadow-elevation-3 transition-all cursor-pointer active:scale-[0.98]">
                            <Plus size={24} />
                            Upload & Stage Photo
                            <input type="file" className="hidden" onChange={handleFileUpload} disabled={uploading} accept="image/*" />
                        </label>
                    </div>
                ) : (
                    <div className="mb-12">
                        <div className="flex items-center gap-2 mb-4">
                            <Sparkles className="text-accent" size={20} />
                            <h2 className="text-xl font-semibold text-primary">Reference Image</h2>
                            <div className="group relative">
                                <Info size={16} className="text-on-surface-muted cursor-help" />
                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-primary text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 shadow-elevation-4">
                                    The first image uploaded to a room becomes the reference.
                                    All other images in this room use it to maintain furniture and style consistency.
                                </div>
                            </div>
                        </div>

                        <div className="bg-white rounded-3xl p-6 shadow-elevation-2 border border-accent/20 flex flex-col lg:flex-row gap-8">
                            <div className="lg:w-2/3 aspect-video rounded-2xl overflow-hidden bg-surface-dim relative group">
                                <img
                                    src={showStaged[referenceImage.id] && referenceImage.latest_result_url ? referenceImage.latest_result_url : referenceImage.original_url}
                                    alt="Reference"
                                    className="w-full h-full object-cover transition-all duration-500"
                                />
                                <div className="absolute top-4 left-4 bg-accent text-white px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5 shadow-elevation-3">
                                    <CheckCircle2 size={14} />
                                    PRIMARY REFERENCE
                                </div>
                                {referenceImage.latest_result_url && (
                                    <button
                                        onClick={() => toggleStaged(referenceImage.id)}
                                        className="absolute bottom-4 left-4 bg-white/90 backdrop-blur text-primary px-4 py-2 rounded-xl text-xs font-bold shadow-elevation-2 hover:bg-white transition-all flex items-center gap-2"
                                    >
                                        <Layers size={14} />
                                        {showStaged[referenceImage.id] ? "VIEW ORIGINAL" : "VIEW STAGED"}
                                    </button>
                                )}
                                <button
                                    onClick={() => handleDeleteImage(referenceImage.id)}
                                    disabled={deleting === referenceImage.id}
                                    className="absolute top-4 right-4 bg-error/90 backdrop-blur text-white p-2 rounded-xl shadow-elevation-2 hover:bg-error transition-all disabled:opacity-50"
                                    title="Delete Image"
                                >
                                    {deleting === referenceImage.id ? <Loader2 size={18} className="animate-spin" /> : <Trash2 size={18} />}
                                </button>
                            </div>
                            <div className="lg:w-1/3 flex flex-col justify-center">
                                <h3 className="text-lg font-bold text-primary mb-2">Reference View</h3>
                                <p className="text-on-surface-variant text-sm mb-6 leading-relaxed">
                                    This is the master view Gemini uses to understand the room's permanent features and your design preferences.
                                </p>
                                <button
                                    onClick={() => handleOpenOptions(referenceImage)}
                                    disabled={startingJob === referenceImage.id}
                                    className="w-full bg-accent hover:bg-accent-700 text-white py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-elevation-2 hover:shadow-elevation-3 disabled:opacity-50"
                                >
                                    <Sparkles size={20} />
                                    Configure & Stage
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Other Angles Gallery */}
                <div>
                    <h2 className="text-xl font-semibold text-primary mb-6 flex items-center gap-2">
                        <Camera className="text-primary-300" size={20} />
                        Other Camera Angles
                    </h2>

                    {otherImages.length === 0 ? (
                        <div className="bg-white rounded-3xl p-12 text-center border-2 border-dashed border-outline-variant">
                            <p className="text-on-surface-variant font-medium">No other angles uploaded yet.</p>
                            <p className="text-sm text-on-surface-muted mt-1">Upload more photos to see consistency in action.</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {otherImages.map((image) => (
                                <div key={image.id} className="bg-white rounded-2xl overflow-hidden shadow-elevation-1 border border-outline-variant group hover:shadow-elevation-4 transition-all">
                                    <div className="aspect-video relative overflow-hidden">
                                        <img
                                            src={showStaged[image.id] && image.latest_result_url ? image.latest_result_url : image.original_url}
                                            alt="Room Angle"
                                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                        />
                                        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
                                            <button
                                                onClick={() => handleOpenOptions(image)}
                                                disabled={startingJob === image.id}
                                                className="bg-white text-primary px-6 py-2.5 rounded-full hover:bg-accent hover:text-white transition-all shadow-elevation-3 font-bold flex items-center gap-2"
                                            >
                                                <Sparkles size={18} />
                                                Stage Angle
                                            </button>
                                        </div>
                                        {image.latest_result_url && (
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    toggleStaged(image.id);
                                                }}
                                                className="absolute bottom-3 right-3 bg-white/90 backdrop-blur text-primary px-3 py-1.5 rounded-lg text-[10px] font-bold shadow-elevation-2 hover:bg-white transition-all flex items-center gap-1.5 z-10"
                                            >
                                                <Layers size={12} />
                                                {showStaged[image.id] ? "ORIGINAL" : "STAGED"}
                                            </button>
                                        )}
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDeleteImage(image.id);
                                            }}
                                            disabled={deleting === image.id}
                                            className="absolute top-3 right-3 bg-error/90 backdrop-blur text-white p-1.5 rounded-lg shadow-elevation-2 hover:bg-error transition-all z-10 disabled:opacity-50"
                                            title="Delete Angle"
                                        >
                                            {deleting === image.id ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                                        </button>
                                    </div>
                                    <div className="p-4 flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <div className="bg-success/10 text-success p-1 rounded-md">
                                                <Layers size={14} />
                                            </div>
                                            <span className="text-sm font-semibold text-primary italic">Consistency Enabled</span>
                                        </div>
                                        <span className="text-[10px] text-on-surface-muted font-bold tracking-tighter uppercase tabular-nums">
                                            {new Date(image.created_at).toLocaleDateString()}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Staging Options Modal */}
                {selectedImage && (
                    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6 animate-fade-in">
                        <div className="absolute inset-0 bg-primary/40 backdrop-blur-sm" onClick={() => setSelectedImage(null)} />
                        <div className="relative bg-white w-full max-w-4xl max-h-[90vh] rounded-3xl shadow-elevation-5 overflow-hidden flex flex-col animate-scale-in">
                            {/* Modal Header */}
                            <div className="px-8 py-6 border-b border-outline-variant flex justify-between items-center bg-surface">
                                <div>
                                    <h2 className="text-2xl font-display font-bold text-primary">Stage this Angle</h2>
                                    <p className="text-sm text-on-surface-variant">Configure your design style and enhancements</p>
                                </div>
                                <button
                                    onClick={() => setSelectedImage(null)}
                                    className="p-2 hover:bg-surface-container rounded-full transition-colors"
                                >
                                    <X size={24} />
                                </button>
                            </div>

                            {/* Modal Content */}
                            <div className="flex-1 overflow-y-auto p-8">
                                <div className="grid lg:grid-cols-2 gap-10">
                                    {/* Left: Preview & Enhancements */}
                                    <div className="space-y-8">
                                        <div className="aspect-video rounded-2xl overflow-hidden shadow-elevation-2 border border-outline-variant">
                                            <img src={selectedImage.original_url} alt="To stage" className="w-full h-full object-cover" />
                                        </div>

                                        <div className="space-y-4">
                                            <h4 className="text-sm font-bold text-on-surface-variant uppercase tracking-wider">Enhancements</h4>
                                            <div className="space-y-3">
                                                <label className="flex items-center gap-3 cursor-pointer group p-3 rounded-xl hover:bg-surface-container transition-colors">
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
                                                    <div className="flex flex-col">
                                                        <span className="text-on-surface font-semibold group-hover:text-primary transition-colors">Fix White Balance</span>
                                                        <span className="text-xs text-on-surface-variant">Automatically correct lighting and color temperature</span>
                                                    </div>
                                                </label>

                                                <label className={`flex items-center gap-3 p-3 rounded-xl transition-colors group ${isSecondaryAngle ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:bg-surface-container'}`}>
                                                    <div className="relative flex items-center">
                                                        <input
                                                            type="checkbox"
                                                            checked={wallDecorations}
                                                            onChange={(e) => !isSecondaryAngle && setWallDecorations(e.target.checked)}
                                                            disabled={isSecondaryAngle}
                                                            className="peer sr-only"
                                                        />
                                                        <div className={`w-5 h-5 border-2 rounded transition-all ${isSecondaryAngle ? 'border-outline-variant bg-surface-container' : 'border-outline peer-checked:bg-primary peer-checked:border-primary'}`} />
                                                        <svg className="absolute w-3.5 h-3.5 text-white left-[3px] opacity-0 peer-checked:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="4">
                                                            <path d="M5 13l4 4L19 7" />
                                                        </svg>
                                                    </div>
                                                    <div className="flex flex-col">
                                                        <span className={`font-semibold transition-colors ${isSecondaryAngle ? 'text-on-surface-variant' : 'text-on-surface group-hover:text-primary'}`}>Wall Decorations</span>
                                                        <span className="text-xs text-on-surface-variant">Add paintings, mirrors, and wall art</span>
                                                    </div>
                                                </label>

                                                <label className={`flex items-center gap-3 p-3 rounded-xl transition-colors group ${isTVDisabled || isSecondaryAngle ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:bg-surface-container'}`}>
                                                    <div className="relative flex items-center">
                                                        <input
                                                            type="checkbox"
                                                            checked={!isTVDisabled && includeTV}
                                                            onChange={(e) => !isTVDisabled && !isSecondaryAngle && setIncludeTV(e.target.checked)}
                                                            disabled={isTVDisabled || isSecondaryAngle}
                                                            className="peer sr-only"
                                                        />
                                                        <div className={`w-5 h-5 border-2 rounded transition-all ${(isTVDisabled || isSecondaryAngle) ? 'border-outline-variant bg-surface-container' : 'border-outline peer-checked:bg-primary peer-checked:border-primary'}`} />
                                                        <svg className="absolute w-3.5 h-3.5 text-white left-[3px] opacity-0 peer-checked:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="4">
                                                            <path d="M5 13l4 4L19 7" />
                                                        </svg>
                                                    </div>
                                                    <div className="flex flex-col">
                                                        <span className={`font-semibold transition-colors ${(isTVDisabled || isSecondaryAngle) ? 'text-on-surface-variant' : 'text-on-surface group-hover:text-primary'}`}>Include TV</span>
                                                        <span className="text-xs text-on-surface-variant">Place a modern flat-screen TV in the room</span>
                                                    </div>
                                                </label>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Right: Style Presets */}
                                    <div>
                                        <h4 className="text-sm font-bold text-on-surface-variant uppercase tracking-wider mb-4">Design Style</h4>
                                        <StylePresets selected={style} onSelect={setStyle} disabled={isSecondaryAngle} />
                                    </div>
                                </div>
                            </div>

                            {/* Modal Footer */}
                            <div className="px-8 py-6 border-t border-outline-variant bg-surface-container flex flex-col sm:flex-row items-center justify-between gap-4">
                                <div className="text-sm text-on-surface-variant italic">
                                    {selectedImage.id !== room.reference_image_id && (
                                        <div className="flex items-center gap-2 text-accent font-medium">
                                            <Layers size={14} />
                                            Reference consistency active
                                        </div>
                                    )}
                                </div>
                                <div className="flex items-center gap-3 w-full sm:w-auto">
                                    <button
                                        onClick={() => setSelectedImage(null)}
                                        className="flex-1 sm:flex-none px-6 py-3 text-on-surface font-semibold hover:bg-surface-container-high rounded-xl transition-colors"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={handleStartStaging}
                                        disabled={startingJob}
                                        className={`
                                            flex-1 sm:flex-none bg-accent hover:bg-accent-700 text-white px-8 py-3 rounded-xl font-bold flex items-center justify-center gap-2 shadow-elevation-3 transition-all active:scale-[0.98]
                                            ${startingJob ? 'opacity-70 animate-pulse cursor-wait' : ''}
                                        `}
                                    >
                                        {startingJob ? (
                                            <Loader2 size={20} className="animate-spin" />
                                        ) : (
                                            <Zap size={20} className="fill-white" />
                                        )}
                                        {startingJob ? 'Initializing...' : 'Start Staging Magic'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
};

export default RoomDetail;
