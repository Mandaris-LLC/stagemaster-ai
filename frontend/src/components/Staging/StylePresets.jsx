import React from 'react';
import { Check } from 'lucide-react';

import styleModern from '../../assets/style-modern.png';
import styleScandinavian from '../../assets/style-scandinavian.png';
import styleIndustrial from '../../assets/style-industrial.png';
import styleMinimalist from '../../assets/style-minimalist.png';
import styleBohemian from '../../assets/style-bohemian.png';
import styleCoastal from '../../assets/style-coastal.png';
import styleFarmhouse from '../../assets/style-farmhouse.png';
import styleLuxury from '../../assets/style-luxury.png';

const styles = [
    {
        id: 'modern',
        name: 'Modern',
        description: 'Clean lines, neutral palette and a minimalist look.',
        image: styleModern
    },
    {
        id: 'scandinavian',
        name: 'Scandinavian',
        description: 'Light, airy, functional & natural materials.',
        image: styleScandinavian
    },
    {
        id: 'industrial',
        name: 'Industrial',
        description: 'Raw materials, urban edge, & high contrast.',
        image: styleIndustrial
    },
    {
        id: 'minimalist',
        name: 'Minimalist',
        description: 'Pure simplicity, essential elements & space.',
        image: styleMinimalist
    },
    {
        id: 'bohemian',
        name: 'Bohemian',
        description: 'Eclectic, vibrant, and full of natural textures and plants.',
        image: styleBohemian
    },
    {
        id: 'coastal',
        name: 'Coastal',
        description: 'Light, breezy, with soft blues and sandy neutrals.',
        image: styleCoastal
    },
    {
        id: 'farmhouse',
        name: 'Farmhouse',
        description: 'Rustic, cozy, and warm with wooden accents.',
        image: styleFarmhouse
    },
    {
        id: 'luxury',
        name: 'Luxury',
        description: 'Sophisticated, opulent, and high-end materials.',
        image: styleLuxury
    },
];

const StylePresets = ({ selected, onSelect }) => {
    return (
        <div className="w-full">
            <div className="grid grid-cols-2 gap-4">
                {styles.map((style) => {
                    const isActive = selected === style.id;
                    return (
                        <button
                            key={style.id}
                            onClick={() => onSelect(style.id)}
                            className={`relative overflow-hidden rounded-xl border text-left transition-all duration-150 group
                                ${isActive
                                    ? 'border-accent ring-2 ring-accent shadow-elevation-3'
                                    : 'border-outline-variant bg-surface hover:border-accent-400 hover:shadow-elevation-2'}`}
                        >
                            {/* Image */}
                            <div className="aspect-[4/3] overflow-hidden">
                                <img
                                    src={style.image}
                                    alt={style.name}
                                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                                />
                            </div>

                            {/* Content */}
                            <div className="p-3 bg-surface">
                                <p className={`text-sm font-semibold mb-0.5 transition-colors duration-150
                                    ${isActive ? 'text-accent-700' : 'text-primary'}`}>
                                    {style.name}
                                </p>
                                <p className="text-xs text-on-surface-variant leading-snug line-clamp-2">
                                    {style.description}
                                </p>
                            </div>

                            {/* Check indicator */}
                            {isActive && (
                                <div className="absolute top-2 right-2 w-6 h-6 bg-accent rounded-full flex items-center justify-center text-white shadow-elevation-2 animate-scale-in">
                                    <Check size={14} strokeWidth={3} />
                                </div>
                            )}
                        </button>
                    );
                })}
            </div>
        </div>
    );
};

export default StylePresets;
