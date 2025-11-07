import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // React ecosystem
          'vendor-react': ['react', 'react-dom', 'react/jsx-runtime'],

          // React Admin (большая библиотека)
          'vendor-react-admin': ['react-admin', 'ra-data-simple-rest'],

          // Material UI (большая библиотека)
          'vendor-mui': [
            '@mui/material',
            '@mui/icons-material',
            '@emotion/react',
            '@emotion/styled',
          ],

          // Material UI Tree View (отдельный пакет)
          'vendor-mui-tree': ['@mui/x-tree-view'],

          // Drag and Drop
          'vendor-dnd': ['@hello-pangea/dnd'],

          // TinyMCE (очень большой редактор)
          'vendor-tinymce': ['@tinymce/tinymce-react', 'tinymce'],

          // KaTeX (для математических формул)
          'vendor-katex': ['katex'],

          // Утилиты
          'vendor-utils': ['react-dropzone', 'use-debounce'],
        },
      },
    },
    // Увеличиваем лимит для chunk size warning до 1000 KB
    chunkSizeWarningLimit: 1000,
  },
})
