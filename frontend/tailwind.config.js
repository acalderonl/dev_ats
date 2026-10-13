/** @type {import('tailwindcss').Config} */

// Paleta de la Academia Naval Almirante Illingworth, tomada de los colores reales de
// anai.edu.ec (no estimados de una captura):
//
//   #0064b4  azul institucional, el dominante del sitio  -> brand-600
//   #003462  azul oscuro de las franjas                  -> brand-900
//   #1ea7fd  celeste de los acentos                      -> brand-400
//   #aad6ff  azul claro de los botones                   -> brand-200
//   #ebf5ff  fondo muy claro                             -> brand-50
//   #20395f  azul del escudo (del propio SVG)            -> escudo
//
// El azul institucional se coloca en el 600 a propósito: toda la interfaz ya usaba
// `brand-600` para botones y acentos, así que la aplicación entera queda con el color
// de la institución sin tocar cada clase una por una.

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#ebf5ff',
          100: '#d6e9ff',
          200: '#aad6ff',
          300: '#7cc3fe',
          400: '#1ea7fd',
          500: '#0d85d6',
          600: '#0064b4',
          700: '#00529b',
          800: '#004480',
          900: '#003462',
          950: '#002241',
        },
        escudo: '#20395f',
      },
    },
  },
  plugins: [],
}
