'use client'

import { useEffect } from 'react'

/**
 * Firefox Sidebar Visibility Fix Component
 * 
 * This component ensures the sidebar is visible in Firefox by:
 * 1. Detecting Firefox browser
 * 2. Forcing display: flex on desktop sizes
 * 3. Monitoring window resize events
 * 
 * Usage: Add this component to the layout or page where the sidebar is used
 */
export default function FirefoxSidebarFix() {
  useEffect(() => {
    // Only run in Firefox
    if (typeof navigator === 'undefined' || !/Firefox/.test(navigator.userAgent)) {
      return
    }

    console.log('🦊 Firefox Sidebar Fix: Initializing...')

    const fixSidebarDisplay = () => {
      // Find sidebar element
      const sidebar = document.querySelector('nav#navigation') as HTMLElement
      
      if (!sidebar) {
        console.warn('🦊 Firefox Sidebar Fix: Sidebar element not found')
        return
      }

      // Check if we're on desktop
      const isDesktop = window.innerWidth >= 1024

      if (isDesktop) {
        // Force display flex
        sidebar.style.display = 'flex'
        sidebar.style.flexDirection = 'column'
        sidebar.style.width = '16rem' // w-64
        sidebar.style.height = '100vh'
        
        // Remove hidden class if present
        sidebar.classList.remove('hidden')
        
        console.log('🦊 Firefox Sidebar Fix: Sidebar display forced to flex', {
          display: sidebar.style.display,
          width: window.innerWidth,
          computedDisplay: window.getComputedStyle(sidebar).display
        })
      } else {
        // On mobile, respect the hidden class
        console.log('🦊 Firefox Sidebar Fix: Mobile view, sidebar should be hidden')
      }
    }

    // Initial fix
    // Use setTimeout to ensure DOM is ready
    setTimeout(fixSidebarDisplay, 0)
    setTimeout(fixSidebarDisplay, 100)
    setTimeout(fixSidebarDisplay, 500)

    // Fix on resize
    window.addEventListener('resize', fixSidebarDisplay)

    // Fix on DOM changes (in case sidebar is dynamically added)
    const observer = new MutationObserver(() => {
      fixSidebarDisplay()
    })

    observer.observe(document.body, {
      childList: true,
      subtree: true
    })

    // Cleanup
    return () => {
      window.removeEventListener('resize', fixSidebarDisplay)
      observer.disconnect()
    }
  }, [])

  // This component doesn't render anything
  return null
}
