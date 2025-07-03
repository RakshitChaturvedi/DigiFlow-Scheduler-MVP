/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Define your custom colors using CSS variables or direct hex codes
        // Matching your design philosophy:
        primaryBlue: '#2563EB',
        primaryGreen: '#16A34A',
        backgroundLight: '#F3F4F6',
        sidebarDark: '#1F2937',
        textDark: '#374151',
        textLight: '#F9FAFB',
        borderColor: '#D1D5DB',
        redAlert: '#EF4444',
        greenSuccess: '#22C55E',
        orangeProgress: '#F97316',
      },
      fontFamily: {
        // Use Inter as the primary font
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}