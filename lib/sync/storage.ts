/**
 * Sync Storage Module
 * Handles user preferences and cross-device synchronization
 */

interface UserPreferences {
  userId: string
  theme: 'light' | 'dark' | 'auto'
  language: string
  notifications: {
    email: boolean
    push: boolean
    desktop: boolean
  }
  dashboard: {
    layout: 'grid' | 'list'
    widgets: string[]
  }
  accessibility: {
    highContrast: boolean
    reducedMotion: boolean
    fontSize: 'small' | 'medium' | 'large'
  }
  lastSync: string
  createdAt: string
  updatedAt: string
}

// In-memory storage for development (replace with database in production)
const userPreferencesStore = new Map<string, UserPreferences>()

export const userPreferences = {
  get: (userId: string): UserPreferences | undefined => {
    return userPreferencesStore.get(userId)
  },
  
  set: (userId: string, preferences: UserPreferences): void => {
    userPreferencesStore.set(userId, preferences)
  },
  
  update: (userId: string, updates: Partial<UserPreferences>): UserPreferences | null => {
    const existing = userPreferencesStore.get(userId)
    if (!existing) return null
    
    const updated = {
      ...existing,
      ...updates,
      updatedAt: new Date().toISOString()
    }
    
    userPreferencesStore.set(userId, updated)
    return updated
  },
  
  delete: (userId: string): boolean => {
    return userPreferencesStore.delete(userId)
  },
  
  clear: (): void => {
    userPreferencesStore.clear()
  }
}

export const getDefaultPreferences = (userId: string): UserPreferences => {
  const now = new Date().toISOString()
  
  return {
    userId,
    theme: 'auto',
    language: 'en',
    notifications: {
      email: true,
      push: true,
      desktop: false
    },
    dashboard: {
      layout: 'grid',
      widgets: ['quick-stats', 'recent-projects', 'alerts', 'performance']
    },
    accessibility: {
      highContrast: false,
      reducedMotion: false,
      fontSize: 'medium'
    },
    lastSync: now,
    createdAt: now,
    updatedAt: now
  }
}

export const syncPreferences = async (userId: string, preferences: UserPreferences): Promise<boolean> => {
  try {
    // In a real implementation, this would sync with a database or external service
    userPreferences.set(userId, {
      ...preferences,
      lastSync: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    })
    
    return true
  } catch (error) {
    console.error('Failed to sync preferences:', error)
    return false
  }
}

export default {
  userPreferences,
  getDefaultPreferences,
  syncPreferences
}