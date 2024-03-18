import express from 'express'
import path from 'path'
import { execSync } from 'child_process'
import * as url from 'url'
import compression from 'compression'

const __dirname = url.fileURLToPath(new URL('.', import.meta.url))

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

    this.app.use((req, res, next) => {
      res.sendFile(path.join(__dirname, '.', 'dist', 'index.html'))
    })
  }
}
const app = new App().app
const port = process.env.PORT || 5000
const server = app.listen(port)
console.log('Server running on port %d', port)
process.on('SIGTERM', () => {
  console.log('SIGTERM signal received: closing HTTP server')
  server.close(() => {
    console.log('HTTP server closed')
  })
})
