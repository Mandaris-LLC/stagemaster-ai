import React from 'react';
import { Link } from 'react-router-dom';
import { Camera } from 'lucide-react';

const Header = () => {
    return (
        <header className="bg-white border-b border-outline-variant sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
                <Link to="/" className="flex items-center gap-3 group">
                    <div className="bg-accent p-2.5 rounded-lg text-white shadow-elevation-2 group-hover:shadow-elevation-3 transition-shadow">
                        <Camera size={22} />
                    </div>
                    <span className="text-xl font-semibold tracking-tight text-primary">
                        StageMaster<span className="text-accent">AI</span>
                    </span>
                </Link>
                <nav className="flex gap-2 items-center">
                    <Link
                        to="/gallery"
                        className="px-4 py-2 text-on-surface-variant hover:text-primary hover:bg-surface-container rounded-md text-sm font-medium transition-colors"
                    >
                        My Gallery
                    </Link>
                    <Link
                        to="#"
                        className="px-4 py-2 text-on-surface-variant hover:text-primary hover:bg-surface-container rounded-md text-sm font-medium transition-colors"
                    >
                        Pricing
                    </Link>
                    <button className="ml-2 bg-accent hover:bg-accent-700 px-5 py-2.5 rounded-lg text-white text-sm font-semibold shadow-elevation-2 hover:shadow-elevation-3 transition-all active:scale-[0.98]">
                        Sign In
                    </button>
                </nav>
            </div>
        </header>
    );
};

export default Header;
