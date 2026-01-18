#!/usr/bin/env node

/**
 * Bundle Size Monitoring Script
 * 
 * Validates that JavaScript bundle sizes stay within performance budgets.
 * Fails the build if bundles exceed defined thresholds.
 * 
 * Requirements: 3.6, 9.5
 * 
 * Usage:
 *   node scripts/check-bundle-size.js
 *   npm run test:bundle
 */

const fs = require('fs')
const path = require('path')

// Performance budgets (in bytes)
const MAX_BUNDLE_SIZE = 1500 * 1024 // 1,500 KiB total JavaScript
const MAX_CHUNK_SIZE = 500 * 1024   // 500 KiB per individual chunk
const WARN_CHUNK_SIZE = 300 * 1024  // 300 KiB warning threshold

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  bold: '\x1b[1m'
}

/**
 * Format bytes to human-readable size
 */
function formatBytes(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KiB', 'MiB', 'GiB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
}

/**
 * Get all JavaScript files from .next/static/chunks directory
 */
function getJavaScriptFiles(buildDir) {
  if (!fs.existsSync(buildDir)) {
    console.error(`${colors.red}${colors.bold}Error:${colors.reset} Build directory not found: ${buildDir}`)
    console.error('Please run "npm run build" first.')
    process.exit(1)
  }

  const files = []
  
  function scanDirectory(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true })
    
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name)
      
      if (entry.isDirectory()) {
        scanDirectory(fullPath)
      } else if (entry.isFile() && entry.name.endsWith('.js')) {
        const stats = fs.statSync(fullPath)
        files.push({
          name: entry.name,
          path: fullPath,
          size: stats.size,
          relativePath: path.relative(buildDir, fullPath)
        })
      }
    }
  }
  
  scanDirectory(buildDir)
  return files
}

/**
 * Analyze bundle sizes and generate report
 */
function analyzeBundles() {
  console.log(`${colors.cyan}${colors.bold}Bundle Size Analysis${colors.reset}`)
  console.log('='.repeat(60))
  console.log()

  const buildDir = path.join(process.cwd(), '.next', 'static', 'chunks')
  const files = getJavaScriptFiles(buildDir)

  if (files.length === 0) {
    console.error(`${colors.red}${colors.bold}Error:${colors.reset} No JavaScript files found in build directory.`)
    console.error('Please run "npm run build" first.')
    process.exit(1)
  }

  // Sort files by size (largest first)
  files.sort((a, b) => b.size - a.size)

  // Calculate total size
  const totalSize = files.reduce((sum, file) => sum + file.size, 0)

  // Track violations
  let hasErrors = false
  let hasWarnings = false

  // Display individual file sizes
  console.log(`${colors.bold}Individual Chunks:${colors.reset}`)
  console.log()

  files.forEach(file => {
    const sizeStr = formatBytes(file.size).padEnd(12)
    const percentage = ((file.size / totalSize) * 100).toFixed(1)
    
    let status = colors.green + '✓' + colors.reset
    let message = ''
    
    if (file.size > MAX_CHUNK_SIZE) {
      status = colors.red + '✗' + colors.reset
      message = colors.red + ` EXCEEDS LIMIT (${formatBytes(MAX_CHUNK_SIZE)})` + colors.reset
      hasErrors = true
    } else if (file.size > WARN_CHUNK_SIZE) {
      status = colors.yellow + '⚠' + colors.reset
      message = colors.yellow + ` WARNING (>${formatBytes(WARN_CHUNK_SIZE)})` + colors.reset
      hasWarnings = true
    }
    
    console.log(`  ${status} ${sizeStr} ${percentage.padStart(5)}%  ${file.relativePath}${message}`)
  })

  console.log()
  console.log('='.repeat(60))
  console.log()

  // Display summary
  console.log(`${colors.bold}Summary:${colors.reset}`)
  console.log()
  console.log(`  Total Files:    ${files.length}`)
  console.log(`  Total Size:     ${formatBytes(totalSize)}`)
  console.log(`  Budget:         ${formatBytes(MAX_BUNDLE_SIZE)}`)
  console.log(`  Remaining:      ${formatBytes(Math.max(0, MAX_BUNDLE_SIZE - totalSize))}`)
  console.log(`  Usage:          ${((totalSize / MAX_BUNDLE_SIZE) * 100).toFixed(1)}%`)
  console.log()

  // Check if total size exceeds budget
  if (totalSize > MAX_BUNDLE_SIZE) {
    const excess = totalSize - MAX_BUNDLE_SIZE
    console.log(`${colors.red}${colors.bold}✗ BUNDLE SIZE EXCEEDED${colors.reset}`)
    console.log(`${colors.red}  Total bundle size ${formatBytes(totalSize)} exceeds limit of ${formatBytes(MAX_BUNDLE_SIZE)}${colors.reset}`)
    console.log(`${colors.red}  Excess: ${formatBytes(excess)} (${((excess / MAX_BUNDLE_SIZE) * 100).toFixed(1)}% over budget)${colors.reset}`)
    console.log()
    hasErrors = true
  } else {
    console.log(`${colors.green}${colors.bold}✓ BUNDLE SIZE OK${colors.reset}`)
    console.log(`${colors.green}  Total bundle size is within budget${colors.reset}`)
    console.log()
  }

  // Display largest chunks
  console.log(`${colors.bold}Top 5 Largest Chunks:${colors.reset}`)
  console.log()
  files.slice(0, 5).forEach((file, index) => {
    const percentage = ((file.size / totalSize) * 100).toFixed(1)
    console.log(`  ${index + 1}. ${formatBytes(file.size).padEnd(12)} (${percentage.padStart(5)}%)  ${file.name}`)
  })
  console.log()

  // Recommendations
  if (hasErrors || hasWarnings) {
    console.log(`${colors.bold}Recommendations:${colors.reset}`)
    console.log()
    
    if (hasErrors) {
      console.log(`  ${colors.red}•${colors.reset} Review large chunks and consider code splitting`)
      console.log(`  ${colors.red}•${colors.reset} Use dynamic imports for non-critical features`)
      console.log(`  ${colors.red}•${colors.reset} Analyze bundle with: npm run build:analyze`)
    }
    
    if (hasWarnings) {
      console.log(`  ${colors.yellow}•${colors.reset} Monitor chunk sizes to prevent future issues`)
      console.log(`  ${colors.yellow}•${colors.reset} Consider lazy loading for large components`)
    }
    
    console.log()
  }

  // Exit with appropriate code
  if (hasErrors) {
    console.log(`${colors.red}${colors.bold}Build failed due to bundle size violations.${colors.reset}`)
    process.exit(1)
  } else if (hasWarnings) {
    console.log(`${colors.yellow}${colors.bold}Build completed with warnings.${colors.reset}`)
    process.exit(0)
  } else {
    console.log(`${colors.green}${colors.bold}All bundle size checks passed!${colors.reset}`)
    process.exit(0)
  }
}

// Run analysis
try {
  analyzeBundles()
} catch (error) {
  console.error(`${colors.red}${colors.bold}Error:${colors.reset} ${error.message}`)
  console.error(error.stack)
  process.exit(1)
}
