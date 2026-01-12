import React, { useState, useEffect } from 'react';
import Header from '../components/Common/Header';
import { Link } from 'react-router-dom';
import { Plus, Image as ImageIcon, Clock, CheckCircle2, AlertCircle, ArrowRight, Loader2, Trash2 } from 'lucide-react';
import api from '../services/api';

const Gallery = () => {
    const [jobs, setJobs] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchJobs = async () => {
            try {
                const response = await api.get('/jobs');
                setJobs(response.data.jobs || []);
            } catch (e) {
                console.error("Failed to fetch jobs");
            } finally {
                setIsLoading(false);
            }
        };
        fetchJobs();
    }, []);

    const handleDelete = async (e, jobId) => {
        // Prevent clicking the parent Link
        e.preventDefault();
        e.stopPropagation();

        if (!window.confirm("Are you sure you want to delete this staging?")) {
            return;
        }

        try {
            await api.delete(`/jobs/${jobId}`);
            setJobs(prevJobs => prevJobs.filter(job => job.id !== jobId));
        } catch (error) {
            console.error("Failed to delete job", error);
            alert("Failed to delete job. Please try again.");
        }
    };

    const getStatusBadge = (status) => {
        switch (status) {
            case 'completed':
                return (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-success/10 text-success text-xs font-semibold">
                        <CheckCircle2 size={12} />
                        Complete
                    </span>
                );
            case 'error':
                return (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-error/10 text-error text-xs font-semibold">
                        <AlertCircle size={12} />
                        Error
                    </span>
                );
            default:
                return (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-warning/10 text-warning text-xs font-semibold">
                        <Loader2 size={12} className="animate-spin" />
                        Processing
                    </span>
                );
        }
    };

    return (
        <div className="min-h-screen bg-surface-dim">
            <Header />
            <main className="max-w-6xl mx-auto px-6 py-12">
                {/* Header */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-6 animate-fade-in">
                    <div>
                        <h1 className="text-3xl font-bold text-primary font-display">My Gallery</h1>
                        <p className="text-on-surface-variant mt-1">Manage your virtually staged photos.</p>
                    </div>
                    <Link
                        to="/"
                        className="inline-flex items-center gap-2 bg-accent hover:bg-accent-700 !text-white px-5 py-3 rounded-xl font-semibold shadow-elevation-2 hover:shadow-elevation-3 transition-all active:scale-[0.98]"
                    >
                        <Plus size={18} className="!text-white" />
                        New Staging
                    </Link>
                </div>

                {/* Content */}
                {isLoading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="bg-surface rounded-xl overflow-hidden border border-outline-variant animate-pulse">
                                <div className="aspect-[4/3] bg-surface-container-high"></div>
                                <div className="p-5 space-y-3">
                                    <div className="h-5 bg-surface-container-high rounded w-3/4"></div>
                                    <div className="h-4 bg-surface-container-high rounded w-1/2"></div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : jobs.length === 0 ? (
                    <div className="text-center py-20 bg-surface border border-outline-variant rounded-2xl max-w-lg mx-auto animate-fade-in">
                        <div className="w-16 h-16 bg-surface-container rounded-xl flex items-center justify-center mx-auto mb-6">
                            <ImageIcon size={28} className="text-on-surface-muted" />
                        </div>
                        <h2 className="text-xl font-semibold text-primary mb-2">No staged photos yet</h2>
                        <p className="text-on-surface-variant mb-8 max-w-sm mx-auto">
                            Upload your first photo to see the magic of AI virtual staging.
                        </p>
                        <Link
                            to="/"
                            className="inline-flex items-center gap-2 bg-accent hover:bg-accent-700 !text-white px-6 py-3 rounded-xl font-semibold shadow-elevation-2 hover:shadow-elevation-3 transition-all active:scale-[0.98]"
                        >
                            <Plus size={18} className="!text-white" />
                            Create your first staging
                        </Link>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-slide-up">
                        {jobs.map(job => (
                            <Link
                                key={job.id}
                                to={`/job/${job.id}`}
                                className="bg-surface border border-outline-variant rounded-xl overflow-hidden hover:border-accent/50 hover:shadow-elevation-3 transition-all group"
                            >
                                <div className="aspect-[4/3] bg-surface-container relative overflow-hidden">
                                    {job.result_url ? (
                                        <img
                                            src={job.result_url}
                                            alt={job.room_type}
                                            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                                        />
                                    ) : (
                                        <div className="absolute inset-0 flex items-center justify-center">
                                            <Loader2 size={24} className="text-on-surface-muted animate-spin" />
                                        </div>
                                    )}

                                    {/* Status Badge */}
                                    <div className="absolute top-3 right-3">
                                        {getStatusBadge(job.status)}
                                    </div>

                                    {/* Hover Overlay */}
                                    <div className="absolute inset-0 bg-accent/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-4">
                                        <div className="bg-white p-3 rounded-full shadow-elevation-3 hover:scale-110 transition-transform">
                                            <ArrowRight size={20} className="text-accent" />
                                        </div>
                                        <button
                                            onClick={(e) => handleDelete(e, job.id)}
                                            className="bg-white p-3 rounded-full shadow-elevation-3 text-error hover:bg-error/10 hover:scale-110 transition-all"
                                            title="Delete staging"
                                        >
                                            <Trash2 size={20} />
                                        </button>
                                    </div>
                                </div>

                                <div className="p-5">
                                    <div className="flex justify-between items-start mb-2">
                                        <h4 className="text-base font-semibold text-primary capitalize group-hover:text-accent transition-colors">
                                            {job.room_type.replace('_', ' ')}
                                        </h4>
                                        <span className="text-xs font-medium text-accent bg-accent/10 px-2 py-0.5 rounded capitalize">
                                            {job.style_preset}
                                        </span>
                                    </div>
                                    <p className="text-xs text-on-surface-muted flex items-center gap-1.5">
                                        <Clock size={12} />
                                        {new Date(job.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                                    </p>
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
};

export default Gallery;
