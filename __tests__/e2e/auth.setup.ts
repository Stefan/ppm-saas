/**
 * Playwright Authentication Setup
 * 
 * This setup script runs before all tests and creates a persistent
 * authentication state that can be reused across all test files.
 */

import { test as setup, expect } from '@playwright/test';
import * as path from 'path';

const authFile = path.join(__dirname, '../../playwright/.auth/user.json');

setup('authenticate', async ({ page }) => {
  const email = process.env.TEST_USER_EMAIL || 'test-e2e@orkivo.com';
  const password = process.env.TEST_USER_PASSWORD || 'TestPassword123!';
  
  console.log('🔐 Starting authentication setup...');
  console.log(`📧 Email: ${email}`);
  
  // Navigate to the app (will redirect to login)
  await page.goto('/');
  await page.waitForLoadState('domcontentloaded');
  
  // Wait for login form
  console.log('⏳ Waiting for login form...');
  await page.waitForSelector('input[type="email"]', { timeout: 15000 });
  
  // Fill in credentials
  console.log('📝 Filling in credentials...');
  await page.locator('input[type="email"]').fill(email);
  await page.locator('input[type="password"]').fill(password);
  
  // Click sign in button
  console.log('🖱️ Clicking sign in...');
  await page.locator('button[type="submit"]').click();
  
  // Wait for successful navigation away from login
  console.log('⏳ Waiting for navigation...');
  await page.waitForURL((url) => {
    const pathname = url.pathname;
    return pathname !== '/' && 
           !pathname.includes('/login') && 
           !pathname.includes('/auth');
  }, { timeout: 30000 });
  
  // Verify we're logged in by checking for a protected page element
  console.log('✅ Login successful!');
  console.log(`📍 Current URL: ${page.url()}`);
  
  // Save authentication state
  console.log('💾 Saving authentication state...');
  await page.context().storageState({ path: authFile });
  
  console.log('✅ Authentication setup complete!');
});
