import ImportMetaEnvPlugin from '@import-meta-env/unplugin'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
import postcss from './postcss.config.js'

// https://vitejs.dev/config/
/** @type {import('vite').UserConfig} */
export default defineConfig(({ mode }) => {
  const env = loadEnv('.env', process.cwd())

  // options from docker build args
  const basePath =
    process.env.VITE_USE_RELATIVE_BASE_URL == 'true' ? '' : undefined
  const buildSourceMaps = process.env.VITE_SKIP_SENTRY_SOURCE_MAP != 'true'

  if (mode === 'default') {
    return {
      plugins: [
        react({ jsxRuntime: 'classic' }),
        ImportMetaEnvPlugin.vite({
          example: '.env.example',
        }),
        // Put the Sentry vite plugin after all other plugins
        ...(buildSourceMaps
          ? [
              {
                name: 'sourcemap-exclude',
                transform(code: string, id: string) {
                  if (id.includes('node_modules')) {
                    return {
                      code,
                      // https://github.com/rollup/rollup/blob/master/docs/plugin-development/index.md#source-code-transformations
                      map: { mappings: '' },
                    }
                  }
                },
              },
            ]
          : []),
      ],
      resolve: {
        alias: {
          '@/': new URL('./src/', import.meta.url).pathname,
        },
      },
      css: {
        postcss,
      },
      envPrefix: [],
      build: {
        minify: 'terser',
        sourcemap: buildSourceMaps,
        rollupOptions: {
          onwarn(warning, warn) {
            if (
              warning.code === 'MODULE_LEVEL_DIRECTIVE' ||
              warning.code === 'SOURCEMAP_ERROR'
            ) {
              return
            }
            warn(warning)
          },
        },
      },
      base: basePath,
      define: {
        'process.env.NODE_DEBUG': false,
      },
      server: {
        hmr: {
            host: "localhost",
            protocol: "ws",
        },
      }
    }
  } else {
    return {
      plugins: [react()],
      resolve: {
        alias: {
          '@/': new URL('./src/', import.meta.url).pathname,
        },
      },
      css: {
        postcss,
      },
      base: basePath,
      define: {
        'process.env.NODE_DEBUG': false,
      },
    }
  }
})
