import { defineConfig }    from 'vite'
import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel               from '@rolldown/plugin-babel'
import { readFileSync, createReadStream } from 'node:fs'
import { resolve, join }   from 'node:path'
import { fileURLToPath }   from 'node:url'

const __dirname = fileURLToPath(new URL('.', import.meta.url))
const ortDist   = resolve(__dirname, 'node_modules/onnxruntime-web/dist')

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    babel({ presets: [reactCompilerPreset()] }),

    // ort-wasm-simd-threaded.mjs must be dynamically import()-able at runtime.
    // Vite blocks import() of files in /public (they're static assets, not modules).
    // Solution: serve it from node_modules in dev via middleware, and emit it to
    // dist/ root on build so it's reachable at /ort-wasm-simd-threaded.mjs.
    {
      name: 'serve-ort-wasm-mjs',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          if (req.url?.split('?')[0] === '/ort-wasm-simd-threaded.mjs') {
            res.setHeader('Content-Type', 'application/javascript; charset=utf-8')
            createReadStream(join(ortDist, 'ort-wasm-simd-threaded.mjs')).pipe(res)
          } else {
            next()
          }
        })
      },
      generateBundle() {
        this.emitFile({
          type:     'asset',
          fileName: 'ort-wasm-simd-threaded.mjs',
          source:   readFileSync(join(ortDist, 'ort-wasm-simd-threaded.mjs'), 'utf-8'),
        })
      },
    },
  ],

  optimizeDeps: {
    // Include onnxruntime-web/wasm so rolldown bundles it with vad-web (CJS→ESM).
    // WASM/MJS paths are controlled at runtime via onnxWASMBasePath: "/" in MicVAD.new().
    include: ['onnxruntime-web/wasm', '@ricky0123/vad-web'],
  },

  // .wasm binaries are loaded via fetch() — serve them as static assets from /public.
  assetsInclude: ['**/*.wasm'],
})
