/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // Material Design 3 - Professional Real Estate Theme
                'primary': {
                    DEFAULT: '#1e293b',  // Deep Navy - trustworthy, professional
                    50: '#f8fafc',
                    100: '#f1f5f9',
                    200: '#e2e8f0',
                    300: '#cbd5e1',
                    400: '#94a3b8',
                    500: '#64748b',
                    600: '#475569',
                    700: '#334155',
                    800: '#1e293b',
                    900: '#0f172a',
                },
                'accent': {
                    DEFAULT: '#0d9488',  // Teal - fresh, modern, premium
                    50: '#f0fdfa',
                    100: '#ccfbf1',
                    200: '#99f6e4',
                    300: '#5eead4',
                    400: '#2dd4bf',
                    500: '#14b8a6',
                    600: '#0d9488',
                    700: '#0f766e',
                    800: '#115e59',
                    900: '#134e4a',
                },
                // Surface colors (Material Design surfaces)
                'surface': {
                    DEFAULT: '#ffffff',
                    dim: '#f8fafc',
                    bright: '#ffffff',
                    container: '#f1f5f9',
                    'container-high': '#e2e8f0',
                    'container-low': '#f8fafc',
                },
                // Semantic colors
                'success': '#059669',
                'warning': '#d97706',
                'error': '#dc2626',
                'info': '#0284c7',
                // Text colors
                'on-surface': '#0f172a',
                'on-surface-variant': '#475569',
                'on-surface-muted': '#94a3b8',
                // Outline
                'outline': '#cbd5e1',
                'outline-variant': '#e2e8f0',
            },
            borderRadius: {
                'sm': '4px',
                'DEFAULT': '8px',
                'md': '12px',
                'lg': '16px',
                'xl': '20px',
                '2xl': '24px',
                '3xl': '28px',
            },
            boxShadow: {
                // Material Design 3 Elevation System
                'elevation-1': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
                'elevation-2': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)',
                'elevation-3': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
                'elevation-4': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
                'elevation-5': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
            },
            fontFamily: {
                'sans': ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
                'display': ['Outfit', 'sans-serif'],
            },
            transitionTimingFunction: {
                'material-standard': 'cubic-bezier(0.2, 0, 0, 1)',
                'material-decelerate': 'cubic-bezier(0, 0, 0, 1)',
                'material-accelerate': 'cubic-bezier(0.3, 0, 1, 1)',
            },
            transitionDuration: {
                'material-short': '150ms',
                'material-medium': '300ms',
                'material-long': '500ms',
            },
            animation: {
                'fade-in': 'fadeIn 0.3s ease-out',
                'slide-up': 'slideUp 0.3s ease-out',
                'scale-in': 'scaleIn 0.2s ease-out',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { transform: 'translateY(8px)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                },
                scaleIn: {
                    '0%': { transform: 'scale(0.95)' },
                    '100%': { transform: 'scale(1)' },
                },
            },
        },
    },
    plugins: [],
}
