import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Home, MapPin, ChevronRight, Loader2 } from 'lucide-react';
import { listProperties, createProperty } from '../services/api';
import Header from '../components/Common/Header';

const Properties = () => {
    const [properties, setProperties] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isAdding, setIsAdding] = useState(false);
    const [newName, setNewName] = useState('');
    const [newAddress, setNewAddress] = useState('');

    useEffect(() => {
        fetchProperties();
    }, []);

    const fetchProperties = async () => {
        try {
            const data = await listProperties();
            setProperties(data);
        } catch (error) {
            console.error("Error fetching properties:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateProperty = async (e) => {
        e.preventDefault();
        if (!newName.trim()) return;

        try {
            await createProperty({ name: newName, address: newAddress });
            setNewName('');
            setNewAddress('');
            setIsAdding(false);
            fetchProperties();
        } catch (error) {
            console.error("Error creating property:", error);
        }
    };

    return (
        <div className="min-h-screen bg-surface-dim">
            <Header />
            <main className="max-w-7xl mx-auto px-6 py-12">
                <div className="flex justify-between items-center mb-10">
                    <div>
                        <h1 className="text-4xl font-display font-bold text-primary mb-2">My Properties</h1>
                        <p className="text-on-surface-variant">Manage your real estate catalog and rooms</p>
                    </div>
                    <button
                        onClick={() => setIsAdding(true)}
                        className="bg-accent hover:bg-accent-700 text-white px-6 py-3 rounded-xl font-semibold flex items-center gap-2 shadow-elevation-2 transition-all active:scale-[0.98]"
                    >
                        <Plus size={20} />
                        Add Property
                    </button>
                </div>

                {isAdding && (
                    <div className="bg-white rounded-2xl p-8 shadow-elevation-3 mb-10 animate-scale-in border border-outline-variant">
                        <h2 className="text-xl font-semibold mb-6 text-primary">New Property</h2>
                        <form onSubmit={handleCreateProperty} className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-on-surface-variant ml-1">Property Name</label>
                                <input
                                    type="text"
                                    placeholder="e.g. Sunnyvale Modern Villa"
                                    className="w-full px-4 py-3 rounded-xl border border-outline focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-all bg-surface-dim"
                                    value={newName}
                                    onChange={(e) => setNewName(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-on-surface-variant ml-1">Address (Optional)</label>
                                <input
                                    type="text"
                                    placeholder="123 Luxury Way, Beverly Hills"
                                    className="w-full px-4 py-3 rounded-xl border border-outline focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-all bg-surface-dim"
                                    value={newAddress}
                                    onChange={(e) => setNewAddress(e.target.value)}
                                />
                            </div>
                            <div className="md:col-span-2 flex justify-end gap-3 mt-4">
                                <button
                                    type="button"
                                    onClick={() => setIsAdding(false)}
                                    className="px-6 py-3 text-on-surface-variant hover:bg-surface-container rounded-xl font-medium transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="bg-primary text-white px-8 py-3 rounded-xl font-semibold shadow-elevation-2 hover:bg-primary-700 transition-all"
                                >
                                    Create Property
                                </button>
                            </div>
                        </form>
                    </div>
                )}

                {loading ? (
                    <div className="flex flex-col items-center justify-center py-20">
                        <Loader2 className="animate-spin text-accent mb-4" size={40} />
                        <p className="text-on-surface-variant font-medium">Loading properties...</p>
                    </div>
                ) : properties.length === 0 ? (
                    <div className="bg-white rounded-3xl p-12 text-center border-2 border-dashed border-outline-variant">
                        <div className="bg-surface-container w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
                            <Home className="text-primary-300" size={32} />
                        </div>
                        <h3 className="text-2xl font-display font-semibold text-primary mb-3">No properties yet</h3>
                        <p className="text-on-surface-variant max-w-md mx-auto mb-8">
                            Create your first property to start organizing your virtual staging projects by room and angle.
                        </p>
                        <button
                            onClick={() => setIsAdding(true)}
                            className="bg-primary text-white px-8 py-3.5 rounded-xl font-semibold inline-flex items-center gap-2 hover:bg-primary-700 transition-all"
                        >
                            <Plus size={20} />
                            Create my first property
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {properties.map((property) => (
                            <Link
                                key={property.id}
                                to={`/property/${property.id}`}
                                className="group bg-white rounded-3xl p-6 shadow-elevation-1 hover:shadow-elevation-4 border border-outline-variant transition-all animate-fade-in"
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div className="bg-primary-50 p-4 rounded-2xl text-primary group-hover:bg-accent group-hover:text-white transition-colors">
                                        <Home size={28} />
                                    </div>
                                    <div className="bg-surface-container px-3 py-1 rounded-full text-xs font-bold text-on-surface-variant tracking-wider uppercase">
                                        Property
                                    </div>
                                </div>
                                <h3 className="text-xl font-display font-bold text-primary mb-2 group-hover:text-accent transition-colors">
                                    {property.name}
                                </h3>
                                <div className="flex items-center gap-2 text-on-surface-variant text-sm mb-6">
                                    <MapPin size={14} />
                                    <span className="truncate">{property.address || 'No address provided'}</span>
                                </div>
                                <div className="pt-4 border-t border-outline-variant flex justify-between items-center text-accent font-semibold">
                                    <span>View property</span>
                                    <ChevronRight size={18} className="group-hover:translate-x-1 transition-transform" />
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
};

export default Properties;
