/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#F7F7F3',
        surface: {
          DEFAULT: '#FFFFFF',
          card: '#FFFFFF',
          subtle: '#FAFAF7',
          border: '#E5E5DF',
          hover: '#F2F2EC',
        },
        charcoal: {
          DEFAULT: '#202A30',
          muted: '#5A626A',
          light: '#8C959D',
        },
        brand: {
          green: '#527D75',
          greenDark: '#3D5E57',
          greenLight: '#EBF2F0',
          blue: '#7899B5',
          blueDark: '#50728F',
          blueLight: '#EEF4F8',
          amber: '#C48A2C',
          amberLight: '#FDF6E9',
          rose: '#B83E3E',
          roseLight: '#FCEEEE',
        },
        aqi: {
          good: '#3D8B7A',
          satisfactory: '#6B9E4E',
          moderate: '#C48A2C',
          poor: '#C26738',
          verypoor: '#B83E3E',
          severe: '#7A2338',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      }
    },
  },
  plugins: [],
}
