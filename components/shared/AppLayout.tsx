'use client'

import React, { useEffect, useRef, useState } from 'react'
import { useAuth } from '../../app/providers/SupabaseAuthProvider'
import { HelpChatProvider } from '../../app/providers/HelpChatProvider'
import { useRouter } from 'next/navigation'
import { Menu } from 'lucide-react'
import Sidebar from '../navigation/Sidebar'
import HelpChat from '../HelpChat'
import HelpChatToggle from '../HelpChatToggle'
import { useScrollPerformance } from '../../hooks/useScrollPerformance'
import { useIsMobile } from '../../hooks/useMediaQuery'
import { 
  chromeScrollPerformanceManager, 
  CHROME_SCROLL_CLASSES 
} from '../../lib/utils/chrome-scroll-performance'

export interface AppLayoutProps {
  children: React.ReactNode
}

export default function AppLayout({ children }: AppLayoutProps) {
  const { session, loading } = useAuth()
  const router = useRouter()
  const mainContentRef = useRef<HTMLElement>(null)
  
  // Mobile sidebar state management
  const isMobile = useIsMobile()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  
  // Chrome browser detection
  const [isChromeBasedBrowser, setIsChromeBasedBrowser] = useState(false)
  
  // Toggle function for mobile sidebar
  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen)
  }

  // Initialize Chrome browser detection
  useEffect(() => {
    // Check if browser is Chrome-based
    const userAgent = window.navigator.userAgent
    const vendor = window.navigator.vendor
    const isChrome = /Chrome/.test(userAgent) && /Google Inc/.test(vendor)
    const isEdge = /Edg/.test(userAgent)
    const isBrave = (window.navigator as any).brave !== undefined
    const isOpera = /OPR/.test(userAgent)
    
    setIsChromeBasedBrowser(isChrome || isEdge || isBrave || isOpera)
  }, [])

  // Initialize Chrome scroll performance optimizations
  useEffect(() => {
    const mainElement = mainContentRef.current
    if (!mainElement || !isChromeBasedBrowser) return

    // Apply Chrome-specific optimizations
    chromeScrollPerformanceManager.applyChromeOptimizations(mainElement)
    
    // Initialize Chrome scroll event handling
    const cleanup = chromeScrollPerformanceManager.initializeChromeScrollHandling(mainElement)
    
    return cleanup
  }, [isChromeBasedBrowser])

  // Initialize scroll performance monitoring
  const {
    performanceSummary,
    isScrolling
  } = useScrollPerformance({
    elementRef: mainContentRef,
    enableMetrics: true,
    enableOptimizations: true,
    debugMode: process.env.NODE_ENV === 'development',
    onScrollStart: () => {
      // Optional: Add scroll start optimizations
      if (process.env.NODE_ENV === 'development') {
        console.log('Scroll started - performance monitoring active')
      }
    },
    onScrollEnd: () => {
      // Optional: Log scroll performance
      if (process.env.NODE_ENV === 'development') {
        console.log('Scroll performance summary:', performanceSummary)
      }
    }
  })

  useEffect(() => {
    if (!loading && !session) {
      console.log('🔒 No session found, redirecting to login...')
      router.push('/')
    }
  }, [session, loading, router])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!session) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <p className="text-gray-600 mb-4">Redirecting to login...</p>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        </div>
      </div>
    )
  }

  return (
    <HelpChatProvider>
      <div className="flex h-screen bg-white layout-optimized chrome-flex-container chrome-flex-gap-prevention chrome-background-coverage"
           style={{
             // Cross-browser flexbox with vendor prefixes
             WebkitBoxSizing: 'border-box',
             MozBoxSizing: 'border-box',
             boxSizing: 'border-box',
             backgroundColor: '#ffffff',
             backgroundAttachment: 'local',
             minHeight: '100vh',
             // Cross-browser gap elimination
             gap: 0,
             margin: 0,
             padding: 0,
             // Cross-browser hardware acceleration
             WebkitTransform: 'translateZ(0)',
             MozTransform: 'translateZ(0)',
             msTransform: 'translateZ(0)',
             transform: 'translateZ(0)',
             willChange: 'transform'
           } as React.CSSProperties}
      >
        {/* Sidebar */}
        <Sidebar 
          isOpen={isMobile ? sidebarOpen : true} 
          onToggle={toggleSidebar}
          isMobile={isMobile}
        />
        
        {/* Main Content */}
        <div className="flex-1 flex flex-col min-w-0 layout-optimized chrome-flex-item chrome-flex-gap-prevention chrome-background-coverage"
             style={{
               // Cross-browser flexbox optimization with vendor prefixes
               WebkitBoxSizing: 'border-box',
               MozBoxSizing: 'border-box',
               boxSizing: 'border-box',
               WebkitFlex: '1 1 0%',
               MsFlex: '1 1 0%',
               flex: '1 1 0%',
               backgroundColor: '#ffffff',
               backgroundAttachment: 'local',
               // Cross-browser gap prevention
               margin: 0,
               padding: 0,
               border: 'none',
               // Cross-browser hardware acceleration
               WebkitTransform: 'translateZ(0)',
               MozTransform: 'translateZ(0)',
               msTransform: 'translateZ(0)',
               transform: 'translateZ(0)',
               willChange: 'transform'
             } as React.CSSProperties}
        >
          {/* Mobile Header with Menu Button */}
          {isMobile && (
            <header className="lg:hidden bg-white border-b border-gray-200 p-4 flex items-center layout-stable">
              <button
                onClick={toggleSidebar}
                className="p-2 rounded-md hover:bg-gray-100 transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center hover-optimized"
              >
                <Menu className="h-6 w-6 text-gray-600" />
              </button>
              <h1 className="ml-3 text-lg font-semibold text-gray-900 text-optimized">PPM Dashboard</h1>
            </header>
          )}
          
          {/* Main Content Area */}
          <main 
            ref={mainContentRef}
            className={`flex-1 min-h-screen bg-white overflow-auto scrollable-container scroll-boundary-fix content-scroll-area dashboard-scroll main-content-optimized dashboard-performance performance-critical chrome-scroll-optimized chrome-background-coverage chrome-flex-item chrome-flex-gap-prevention chrome-boundary-fix ${CHROME_SCROLL_CLASSES.PERFORMANCE} ${CHROME_SCROLL_CLASSES.CONTAINER_PERFORMANCE} ${CHROME_SCROLL_CLASSES.MAIN_CONTENT_PERFORMANCE} ${CHROME_SCROLL_CLASSES.BACKGROUND_CONSISTENCY} ${CHROME_SCROLL_CLASSES.SCROLL_STATE_BACKGROUND} ${CHROME_SCROLL_CLASSES.MOMENTUM_ARTIFACT_PREVENTION} ${CHROME_SCROLL_CLASSES.SCROLL_EVENTS} ${isScrolling ? 'scrolling' : ''} ${isMobile ? `mobile-performance chrome-mobile-optimized ${CHROME_SCROLL_CLASSES.MOBILE_PERFORMANCE}` : `chrome-desktop-optimized ${CHROME_SCROLL_CLASSES.DESKTOP_PERFORMANCE}`}`}

            style={{
              // Cross-browser scroll optimizations with vendor prefixes
              WebkitOverflowScrolling: 'touch',
              overscrollBehavior: 'contain',
              overscrollBehaviorY: 'contain',
              WebkitOverscrollBehavior: 'contain',
              MozOverscrollBehavior: 'contain',
              msOverscrollBehavior: 'contain',
              
              // Cross-browser will-change properties for scroll optimization (Task 5)
              willChange: isScrolling ? 'scroll-position, transform' : 'scroll-position',
              WebkitWillChange: isScrolling ? 'scroll-position, transform' : 'scroll-position',
              
              // Cross-browser contain properties for layout optimization (Task 5)
              contain: 'layout style paint',
              
              // Cross-browser background coverage and overscroll containment
              backgroundColor: '#ffffff',
              backgroundAttachment: 'local',
              WebkitBackgroundAttachment: 'local',
              backgroundImage: 'linear-gradient(to bottom, #ffffff 0%, #ffffff 100%)',
              minHeight: '100vh',
              
              // Cross-browser hardware acceleration and performance
              WebkitTransform: 'translateZ(0)',
              MozTransform: 'translateZ(0)',
              msTransform: 'translateZ(0)',
              transform: 'translateZ(0)',
              
              // Cross-browser layout containment and optimization
              WebkitBackfaceVisibility: 'hidden',
              MozBackfaceVisibility: 'hidden',
              msBackfaceVisibility: 'hidden',
              backfaceVisibility: 'hidden',
              
              // Cross-browser flexbox optimization and gap prevention
              WebkitBoxSizing: 'border-box',
              MozBoxSizing: 'border-box',
              boxSizing: 'border-box',
              WebkitFlex: '1 1 0%',
              MsFlex: '1 1 0%',
              flex: '1 1 0%',
              margin: 0,
              padding: 0,
              border: 'none'
            } as React.CSSProperties}
          >
            {children}
          </main>
        </div>

        {/* Help Chat Integration */}
        <HelpChat />
        <HelpChatToggle />
      </div>
    </HelpChatProvider>
  )
}