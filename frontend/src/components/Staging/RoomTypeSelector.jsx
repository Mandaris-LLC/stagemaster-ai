import React from 'react';
import { Sofa, Bed, Utensils, Coffee, Monitor, Bath } from 'lucide-react';

const roomTypes = [
    { id: 'living_room', name: 'Living Room', icon: Sofa },
    { id: 'bedroom', name: 'Bedroom', icon: Bed },
    { id: 'bathroom', name: 'Bathroom', icon: Bath },
    { id: 'kitchen', name: 'Kitchen', icon: Coffee },
    { id: 'dining_room', name: 'Dining Room', icon: Utensils },
    { id: 'office', name: 'Office', icon: Monitor },
];

const RoomTypeSelector = ({ selected, onSelect }) => {
    return (
        <div className="w-full space-y-2">
            {roomTypes.map((type) => {
                const Icon = type.icon;
                const isActive = selected === type.id;
                return (
                    <button
                        key={type.id}
                        onClick={() => onSelect(type.id)}
                        className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl border-2 transition-all duration-150
                            ${isActive
                                ? 'border-teal-600 bg-teal-600 text-white shadow-elevation-2'
                                : 'border-gray-200 bg-white hover:border-teal-400 text-gray-800'}`}
                    >
                        <Icon size={18} className={isActive ? 'text-white' : 'text-on-surface-variant'} />
                        <span className="text-sm font-medium">{type.name}</span>
                    </button>
                );
            })}
        </div>
    );
};

export default RoomTypeSelector;
