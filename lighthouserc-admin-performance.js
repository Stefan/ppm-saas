/**
 * Lighthouse CI Configuration - Admin Performance Page Only
 * Focused testing for admin performance optimization validation
 */

module.exports = {
  ci: {
    collect: {
      // Test only the admin performance page
      url: [
        'http://localhost:3000/admin/performance'
      ],
      
      // Collection settings
      numberOfRuns: 3,
      
      // Chrome settings for consistent testing
      settings: {
        chromeFlags: [
          '--no-sandbox',
          '--disable-dev-shm-usage',
          '--disable-gpu'
        ],
        
        // Desktop testing for admin page
        emulatedFormFactor: 'desktop',
        throttling: {
          rttMs: 40,
          throughputKbps: 10240,
          cpuSlowdownMultiplier: 1
        },
        
        // Skip certain audits that aren't relevant
        skipAudits: [
          'canonical',
          'robots-txt',
          'uses-http2'
        ]
      }
    },
    
    assert: {
      // Performance budgets for admin performance page
      assertions: {
        // Core Web Vitals thresholds (from requirements)
        'first-contentful-paint': ['error', { maxNumericValue: 1500 }],
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        'total-blocking-time': ['error', { maxNumericValue: 200 }],
        'interactive': ['error', { maxNumericValue: 3500 }],
        
        // Performance score
        'categories:performance': ['warn', { minScore: 0.9 }],
        
        // Accessibility and best practices
        'categories:accessibility': ['warn', { minScore: 0.9 }],
        'categories:best-practices': ['warn', { minScore: 0.9 }]
      }
    },
    
    upload: {
      target: 'temporary-public-storage'
    }
  }
}
