import express from 'express'
import path from 'path'
import { execSync } from 'child_process'
import { createProxyMiddleware } from 'http-proxy-middleware'
import * as url from 'url'
import compression from 'compression'

const __dirname = url.fileURLToPath(new URL('.', import.meta.url))

const wsProxy = createProxyMiddleware({
  target:
    process.env.NATS_URL ||
    'ws://truefoundry-nats.truefoundry.svc.cluster.local:443',
  changeOrigin: true,
})

class App {
  app = null
  constructor() {
    try {
      const stdout = execSync('yarn import-meta-env --example .env.example')
      console.log(stdout.toString())
    } catch (error) {
      console.log(error.stdout.toString())
      process.exit(1)
    }
    this.app = express()
    this.config()
  }
  config() {
    this.app.use(compression())
    // Render the dist folder statically
    this.app.use(express.static(path.join(__dirname, '.', 'dist')))

    // Proxy for the connection servicefoundry server
    this.app.use(
      '/api/svc',
      createProxyMiddleware({
        target:
          process.env.SERVICEFOUNDRY_SERVER_URL ||
          'http://truefoundry-servicefoundry-server.truefoundry.svc.cluster.local:3000',
        changeOrigin: true,
        timeout: 60000,
        proxyTimeout: 60000,
        pathRewrite: {
          [`^/api/svc`]: '',
        },
        logLevel: 'debug',
      })
    )

    // Proxy for the connection servicefoundry server socket
    this.app.use(
      '/api/svc/socket.io',
      createProxyMiddleware({
        target:
          process.env.SERVICEFOUNDRY_SERVER_URL ||
          'http://truefoundry-servicefoundry-server.truefoundry.svc.cluster.local:3000',
        changeOrigin: true,
        timeout: 60000,
        proxyTimeout: 60000,
        ws: true,
        pathRewrite: {
          [`^/api/svc/socket.io`]: '/socket.io',
        },
        logLevel: 'debug',
      })
    )
    // Proxy for the connection to mlfoundry-server
    this.app.use(
      '/api/ml',
      createProxyMiddleware({
        target:
          process.env.MLFOUNDRY_SERVER_URL ||
          'http://truefoundry-mlfoundry-server.truefoundry.svc.cluster.local:5000',
        changeOrigin: true,
        pathRewrite: {
          [`^/api/ml`]: '',
        },
        timeout: 60000,
        proxyTimeout: 60000,
        logLevel: 'debug',
      })
    )

    // Proxy for the connection to monitoring-server
    this.app.use(
      '/api/monitoring',
      createProxyMiddleware({
        target:
          process.env.MONITORINGFOUNDRY_SERVER_URL ||
          'http://truefoundry-ml-monitoring-server.truefoundry.svc.cluster.local:8000',
        changeOrigin: true,
        timeout: 60000,
        proxyTimeout: 60000,
        pathRewrite: {
          [`^/api/monitoring`]: '',
        },
        logLevel: 'debug',
      })
    )

    // Proxy for the connection to tfy-build
    this.app.use(
      '/api/tfy-build',
      createProxyMiddleware({
        target:
          process.env.TFY_BUILD_SERVER_URL ||
          'http://truefoundry-tfy-build.truefoundry.svc.cluster.local:5000',
        changeOrigin: true,
        timeout: 60000,
        proxyTimeout: 60000,
        pathRewrite: {
          [`^/api/tfy-build`]: '',
        },
        logLevel: 'debug',
      })
    )

    this.app.get('/readyz', (req, res) =>
      res.status(200).json({ status: 'ok' })
    )
    this.app.get('/livez', (req, res) => res.status(200).json({ status: 'ok' }))

    this.app.use((req, res, next) => {
      res.sendFile(path.join(__dirname, '.', 'dist', 'index.html'))
    })
    this.app.use(wsProxy)
  }
}
const app = new App().app
const port = process.env.PORT || 5000
const server = app.listen(port)
server.on('upgrade', wsProxy.upgrade)
console.log('Server running on port %d', port)
process.on('SIGTERM', () => {
  console.log('SIGTERM signal received: closing HTTP server')
  server.close(() => {
    console.log('HTTP server closed')
  })
})
