/**
 * Deprecated API Detection Utility
 * Detects usage of deprecated browser APIs and provides modern alternatives
 */

export interface DeprecatedAPICheck {
  api: string
  category: 'event' | 'dom' | 'css' | 'storage' | 'other'
  isDeprecated: boolean
  modernAlternative?: string
  reason?: string
}

/**
 * List of deprecated browser APIs based on MDN documentation
 */
const DEPRECATED_APIS = {
  // Deprecated event handling
  event: [
    'attachEvent',
    'detachEvent',
    'createEvent',
    'initEvent',
    'initMouseEvent',
    'initKeyboardEvent',
    'keyCode',
    'which',
    'charCode',
    'returnValue',
    'srcElement'
  ],
  
  // Deprecated DOM manipulation
  dom: [
    'document.write',
    'document.writeln',
    'document.clear',
    'document.captureEvents',
    'document.releaseEvents',
    'createAttribute',
    'getAttributeNode',
    'setAttributeNode',
    'removeAttributeNode'
  ],
  
  // Deprecated CSS properties (vendor-specific that should use autoprefixer)
  css: [
    '-webkit-box-reflect',
    '-moz-appearance',
    '-webkit-mask-box-image',
    'zoom' // Non-standard
  ],
  
  // Deprecated storage/cookie methods
  storage: [
    'localStorage.setItem', // Not deprecated, but needs error handling
    'sessionStorage.setItem' // Not deprecated, but needs error handling
  ],
  
  // Other deprecated APIs
  other: [
    'showModalDialog',
    'createPopup',
    'execCommand',
    'queryCommandEnabled',
    'queryCommandState',
    'queryCommandSupported'
  ]
}

/**
 * Modern alternatives for deprecated APIs
 */
const MODERN_ALTERNATIVES: Record<string, string> = {
  'attachEvent': 'addEventListener',
  'detachEvent': 'removeEventListener',
  'createEvent': 'new Event() or new CustomEvent()',
  'initEvent': 'Event constructor with options',
  'keyCode': 'event.key or event.code',
  'which': 'event.key or event.code',
  'charCode': 'event.key',
  'returnValue': 'event.preventDefault()',
  'srcElement': 'event.target',
  'document.write': 'DOM manipulation methods (appendChild, insertBefore)',
  'document.writeln': 'DOM manipulation methods',
  'showModalDialog': 'dialog element or custom modal',
  'execCommand': 'Clipboard API or contenteditable with modern APIs'
}

/**
 * Check if an API is deprecated
 */
export function isAPIDeprecated(apiName: string): DeprecatedAPICheck {
  // Normalize API name
  const normalizedAPI = apiName.toLowerCase().trim()
  
  // Check each category
  for (const [category, apis] of Object.entries(DEPRECATED_APIS)) {
    const found = apis.find(api => {
      const normalizedDeprecatedAPI = api.toLowerCase()
      // Exact match or the API name contains the deprecated API as a whole word
      return normalizedAPI === normalizedDeprecatedAPI || 
             normalizedDeprecatedAPI === normalizedAPI
    })
    
    if (found) {
      const modernAlt = MODERN_ALTERNATIVES[found] || MODERN_ALTERNATIVES[apiName]
      return {
        api: apiName,
        category: category as DeprecatedAPICheck['category'],
        isDeprecated: true,
        modernAlternative: modernAlt || '',
        reason: `This API is deprecated according to MDN documentation`
      }
    }
  }
  
  return {
    api: apiName,
    category: 'other',
    isDeprecated: false
  }
}

/**
 * Scan code for deprecated API usage
 */
export function scanCodeForDeprecatedAPIs(code: string): DeprecatedAPICheck[] {
  const results: DeprecatedAPICheck[] = []
  const allDeprecatedAPIs = Object.values(DEPRECATED_APIS).flat()
  
  for (const api of allDeprecatedAPIs) {
    // Create regex to find API usage
    const regex = new RegExp(`\\b${api.replace('.', '\\.')}\\b`, 'gi')
    
    if (regex.test(code)) {
      const check = isAPIDeprecated(api)
      if (check.isDeprecated) {
        results.push(check)
      }
    }
  }
  
  return results
}

/**
 * Validate that code uses modern event handling patterns
 */
export function usesModernEventHandling(code: string): boolean {
  // Check for deprecated event handling patterns
  const deprecatedPatterns = [
    /\battachEvent\b/,
    /\bdetachEvent\b/,
    /\bcreateEvent\b/,
    /\binitEvent\b/,
    /\bkeyCode\b/,
    /\bwhich\b/,
    /\bcharCode\b/,
    /\breturnValue\s*=/,
    /\bsrcElement\b/
  ]
  
  // If any deprecated pattern is found, return false
  for (const pattern of deprecatedPatterns) {
    if (pattern.test(code)) {
      return false
    }
  }
  
  return true
}

/**
 * Validate that code uses modern DOM manipulation
 */
export function usesModernDOMManipulation(code: string): boolean {
  // Check for deprecated DOM methods
  const deprecatedPatterns = [
    /\bdocument\.write\b/,
    /\bdocument\.writeln\b/,
    /\bdocument\.clear\b/,
    /\bdocument\.captureEvents\b/,
    /\bdocument\.releaseEvents\b/
  ]
  
  // If any deprecated pattern is found, return false
  for (const pattern of deprecatedPatterns) {
    if (pattern.test(code)) {
      return false
    }
  }
  
  return true
}

/**
 * Validate that code avoids deprecated CSS properties
 */
export function avoidsDeprecatedCSSProperties(cssCode: string): boolean {
  // Check for deprecated vendor-specific properties that should use autoprefixer
  const deprecatedCSSPattern = /-webkit-box-reflect|-moz-appearance|-webkit-mask-box-image|(?<!-)zoom(?=:)/
  
  return !deprecatedCSSPattern.test(cssCode)
}

/**
 * Get all deprecated APIs by category
 */
export function getDeprecatedAPIsByCategory(category: DeprecatedAPICheck['category']): string[] {
  return DEPRECATED_APIS[category] || []
}

/**
 * Check if browser supports modern alternatives
 */
export function supportsModernAlternatives(): {
  addEventListener: boolean
  customEvent: boolean
  clipboardAPI: boolean
  dialogElement: boolean
} {
  if (typeof window === 'undefined') {
    return {
      addEventListener: false,
      customEvent: false,
      clipboardAPI: false,
      dialogElement: false
    }
  }
  
  return {
    addEventListener: 'addEventListener' in window,
    customEvent: typeof CustomEvent !== 'undefined',
    clipboardAPI: 'clipboard' in navigator,
    dialogElement: 'HTMLDialogElement' in window
  }
}
