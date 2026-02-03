import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Plus, LayoutGrid, ChevronRight, Loader2, ArrowLeft, MoreVertical, Layers } from 'lucide-react';
import { getProperty, createRoom } from '../services/api';
import Header from '../components/Common/Header';

const PropertyDetail = () => {
    const { propertyId } = useParams();
    const [property, setProperty] = useState(null);
    const [loading, setLoading] = useState(true);
    const [isAdding, setIsAdding] = useState(false);
    const [newName, setNewName] = useState('');
    const [newType, setNewType] = useState('Living Room');

    const roomTypes = [
        'Living Room', 'Kitchen', 'Bedroom', 'Bathroom',
        'Dining Room', 'Home Office', 'Outdoor', 'Other'
    ];

    useEffect(() => {
        fetchProperty();
    }, [propertyId]);

    const fetchProperty = async () => {
        try {
            const data = await getProperty(propertyId);
            setProperty(data);
        } catch (error) {
            console.error("Error fetching property:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateRoom = async (e) => {
        e.preventDefault();
        if (!newName.trim()) return;

        try {
            await createRoom(propertyId, { name: newName, room_type: newType });
            setNewName('');
            setIsAdding(false);
            fetchProperty();
        } catch (error) {
            console.error("Error creating room:", error);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-surface-dim">
                <Header />
                <div className="flex flex-col items-center justify-center py-40">
                    <Loader2 className="animate-spin text-accent mb-4" size={40} />
                    <p className="text-on-surface-variant font-medium">Loading property details...</p>
                </div>
            </div>
        );
    }

    if (!property) {
        return (
            <div className="min-h-screen bg-surface-dim">
                <Header />
                <div className="max-w-7xl mx-auto px-6 py-12 text-center">
                    <h1 className="text-3xl font-display font-bold text-primary mb-4">Property not found</h1>
                    <Link to="/properties" className="text-accent font-semibold flex items-center justify-center gap-2">
                        <ArrowLeft size={20} />
                        Back to Properties
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-surface-dim">
            <Header />
            <main className="max-w-7xl mx-auto px-6 py-12">
                <div className="mb-10">
                    <Link to="/properties" className="text-on-surface-variant hover:text-primary flex items-center gap-2 text-sm font-medium mb-4 transition-colors">
                        <ArrowLeft size={16} />
                        Back to Properties
                    </Link>
                    <div className="flex justify-between items-end">
                        <div>
                            <h1 className="text-4xl font-display font-bold text-primary mb-2">{property.name}</h1>
                            <p className="text-on-surface-variant flex items-center gap-2">
                                <LayoutGrid size={16} />
                                {property.rooms?.length || 0} Rooms defined in this property
                            </p>
                        </div>
                        <button
                            onClick={() => setIsAdding(true)}
                            className="bg-accent hover:bg-accent-700 text-white px-6 py-3 rounded-xl font-semibold flex items-center gap-2 shadow-elevation-2 transition-all active:scale-[0.98]"
                        >
                            <Plus size={20} />
                            Add New Room
                        </button>
                    </div>
                </div>

                {isAdding && (
                    <div className="bg-white rounded-2xl p-8 shadow-elevation-3 mb-10 animate-scale-in border border-outline-variant">
                        <h2 className="text-xl font-semibold mb-6 text-primary">New Room</h2>
                        <form onSubmit={handleCreateRoom} className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-on-surface-variant ml-1">Room Name</label>
                                <input
                                    type="text"
                                    placeholder="e.g. Master Living Area"
                                    className="w-full px-4 py-3 rounded-xl border border-outline focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-all bg-surface-dim"
                                    value={newName}
                                    onChange={(e) => setNewName(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-on-surface-variant ml-1">Room Type</label>
                                <select
                                    className="w-full px-4 py-3 rounded-xl border border-outline focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-all bg-surface-dim appearance-none"
                                    value={newType}
                                    onChange={(e) => setNewType(e.target.value)}
                                >
                                    {roomTypes.map(type => (
                                        <option key={type} value={type}>{type}</option>
                                    ))}
                                </select>
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
                                    Create Room
                                </button>
                            </div>
                        </form>
                    </div>
                )}

                {property.rooms?.length === 0 ? (
                    <div className="bg-white rounded-3xl p-16 text-center border-2 border-dashed border-outline-variant">
                        <div className="bg-surface-container w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
                            <Plus className="text-primary-300" size={32} />
                        </div>
                        <h3 className="text-2xl font-display font-semibold text-primary mb-3">No rooms created yet</h3>
                        <p className="text-on-surface-variant max-w-md mx-auto mb-8">
                            Each room can hold multiple images from different angles. The first one will be your reference image.
                        </p>
                        <button
                            onClick={() => setIsAdding(true)}
                            className="bg-accent text-white px-8 py-3.5 rounded-xl font-semibold inline-flex items-center gap-2 hover:bg-accent-700 transition-all"
                        >
                            <Plus size={20} />
                            Add your first room
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {property.rooms?.map((room) => (
                            <Link
                                key={room.id}
                                to={`/room/${room.id}`}
                                className="group bg-white rounded-3xl p-6 shadow-elevation-1 hover:shadow-elevation-4 border border-outline-variant transition-all animate-fade-in flex items-center justify-between"
                            >
                                <div className="flex items-center gap-5">
                                    <div className="bg-accent-50 p-4 rounded-2xl text-accent group-hover:bg-accent group-hover:text-white transition-colors">
                                        <Layers size={24} />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold text-primary mb-0.5 group-hover:text-accent transition-colors">
                                            {room.name}
                                        </h3>
                                        <p className="text-on-surface-variant text-sm font-medium">{room.room_type}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    {room.reference_image_id && (
                                        <span className="bg-success/10 text-success text-[10px] font-bold px-2 py-1 rounded-full uppercase tracking-wider">
                                            Ref Set
                                        </span>
                                    )}
                                    <ChevronRight size={20} className="text-on-surface-variant group-hover:translate-x-1 group-hover:text-accent transition-all" />
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
};

export default PropertyDetail;
