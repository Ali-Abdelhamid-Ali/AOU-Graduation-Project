import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

const blockFigmaPrototypeImports = () => ({
  name: 'block-figma-prototype-imports',
  resolveId(source, importer) {
    if (!importer || !source.includes('/FIGMA/')) {
      return null
    }

    throw new Error(
      `FIGMA prototype modules are excluded from production builds: ${source}`
    )
  },
})

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, __dirname, '')
  const apiProxyTarget = env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000'

  return {
    plugins: [
      react(),
      command === 'build' ? blockFigmaPrototypeImports() : null,
    ].filter(Boolean),
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    build: {
      chunkSizeWarningLimit: 500,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) return undefined
            if (id.includes('@kitware/vtk.js')) return 'imaging-vendor'
            if (
              id.includes('three') ||
              id.includes('@react-three/fiber') ||
              id.includes('@react-three/drei')
            ) {
              return 'three-vendor'
            }
            if (
              id.includes('react') ||
              id.includes('react-dom') ||
              id.includes('react-router-dom') ||
              id.includes('framer-motion')
            ) {
              return 'react-vendor'
            }
            return 'vendor'
          },
        },
      },
    },
    test: {
      environment: 'happy-dom',
      setupFiles: './src/test/setup.js',
    },
    server: {
      port: 5173,
      open: true,
      proxy: {
        '/api': {
          target: apiProxyTarget,
          changeOrigin: true,
          rewrite: (requestPath) => requestPath.replace(/^\/api/, ''),
        },
      },
    },
  }
})
