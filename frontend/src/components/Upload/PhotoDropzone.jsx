import React, { useState } from 'react';
import { Camera, Image as ImageIcon, Trash2 } from 'lucide-react';

const PhotoDropzone = ({ onFileSelect, selectedFile, onClear }) => {
    const [dragActive, setDragActive] = useState(false);

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            onFileSelect(e.dataTransfer.files[0]);
        }
    };

    const handleChange = (e) => {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            onFileSelect(e.target.files[0]);
        }
    };

    // Show selected file state
    if (selectedFile) {
        return (
            <div className="p-4 bg-accent-50 border-2 border-accent border-dashed rounded-xl">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 min-w-0">
                        <div className="p-2 bg-accent rounded-lg text-white shrink-0">
                            <Camera size={18} />
                        </div>
                        <span className="text-sm font-medium text-accent-700 truncate">{selectedFile.name}</span>
                    </div>
                    <button
                        onClick={onClear}
                        className="text-on-surface-muted hover:text-error p-2 rounded-lg hover:bg-error/10 transition-colors shrink-0"
                    >
                        <Trash2 size={18} />
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="w-full">
            <div
                className={`relative border-2 border-dashed rounded-xl transition-all duration-150 flex flex-col items-center justify-center p-6 text-center cursor-pointer group
                    ${dragActive
                        ? 'border-accent bg-accent-50'
                        : 'border-outline bg-surface hover:border-accent-400 hover:bg-surface-container-low'}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
            >
                <div className={`mb-3 p-3 rounded-xl transition-all duration-150 ${dragActive
                    ? 'bg-accent text-white scale-110'
                    : 'bg-surface-container text-on-surface-muted group-hover:text-accent'}`}>
                    <Camera size={24} />
                </div>

                <h4 className="text-base font-semibold text-primary mb-1">Import Room Photo</h4>
                <p className="text-on-surface-variant text-sm mb-3">
                    {dragActive ? 'Drop your photo here' : 'Drag and drop or click to browse'}
                </p>

                <div className="flex items-center gap-3 text-xs font-medium text-on-surface-muted">
                    <span className="flex items-center gap-1.5">
                        <ImageIcon size={14} />
                        JPG, PNG
                    </span>
                    <span className="w-1 h-1 bg-on-surface-muted rounded-full"></span>
                    <span>Max 25MB</span>
                </div>

                <input
                    type="file"
                    id="file-upload"
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    accept="image/*"
                    onChange={handleChange}
                />
            </div>
        </div>
    );
};

export default PhotoDropzone;
