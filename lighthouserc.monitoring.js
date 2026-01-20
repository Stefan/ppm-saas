/**
 * Lighthouse CI Monitoring Configuration
 * Extended configuration for continuous performance monitoring
 */

module.exports = {
  ci: {
    collect: {
      // URLs to monitor
      url: [
        'http://localhost:3000/',
        'http://localhost:3000/dashboards',
        'http://localhost:3000/reports',
        'http://localhost:3000/resources',
        'http://localhost:3000/risks',
        'http://localhost:3000/scenarios'
      ],
      
      // Collection settings for monitoring
      numberOfRuns: 3,
      startServerCommand: 'npm run build && npm run start',
      startServerReadyPattern: 'ready on',
      startServerReadyTimeout: 60000,
      
      // Chrome settings
      settings: {
        chromeFlags: [
          '--no-sandbox',
          '--disable-dev-shm-usage',
          '--disable-gpu',
          '--headless'
        ],
        emulatedFormFactor: 'desktop',
        throttling: {
          rttMs: 40,
          throughputKbps: 10240,
          cpuSlowdownMultiplier: 1
        },
        skipAudits: [
          'canonical',
          'robots-txt'
        ]
      }
    },
    
    assert: {
      // Monitoring thresholds - more lenient for CI
      assertions: {
        'categories:performance': ['warn', { minScore: 0.6 }],
        'categories:accessibility': ['warn', { minScore: 0.8 }],
        'categories:best-practices': ['warn', { minScore: 0.8 }],
        'categories:seo': ['warn', { minScore: 0.7 }],
        
        // Core Web Vitals
        'first-contentful-paint': ['warn', { maxNumericValue: 3000 }],
        'largest-contentful-paint': ['warn', { maxNumericValue: 5000 }],
        'cumulative-layout-shift': ['warn', { maxNumericValue: 0.15 }],
        'total-blocking-time': ['warn', { maxNumericValue: 500 }],
        'interactive': ['warn', { maxNumericValue: 6000 }],
        
        // Resource budgets
        'resource-summary:script:size': ['warn', { maxNumericValue: 1000000 }],
        'resource-summary:total:size': ['warn', { maxNumericValue: 4000000 }]
      }
    },
    
    upload: {
      target: 'temporary-public-storage',
      githubAppToken: process.env.LHCI_GITHUB_APP_TOKEN,
      githubToken: process.env.GITHUB_TOKEN
    }
  }
}
