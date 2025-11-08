import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    'process.env': {},
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          // Упрощенное разделение для избежания ошибок
          if (id.includes('node_modules')) {
            // TinyMCE в отдельный чанк (очень большой)
            if (id.includes('tinymce')) {
              return 'vendor-tinymce';
            }

            // KaTeX в отдельный чанк
            if (id.includes('katex')) {
              return 'vendor-katex';
            }

            // Все остальное в один vendor чанк
            return 'vendor';
          }
        },
      },
    },
    // Увеличиваем лимит для chunk size warning до 2000 KB
    chunkSizeWarningLimit: 2000,
  },
})
