/**
 * Unit Test: ESLint Deprecated API Rules
 * Validates that ESLint rules correctly flag deprecated API usage
 * 
 * Note: ESLint's no-restricted-properties rule has limitations with dynamic
 * property access and type inference. These tests validate what ESLint can
 * statically detect.
 */

import { execSync } from 'child_process'
import * as fs from 'fs'
import * as path from 'path'
import * as os from 'os'

describe('ESLint Deprecated API Rules', () => {
  let tempDir: string
  let tempFile: string

  beforeEach(() => {
    // Create a temporary directory for test files within the project
    tempDir = path.join(process.cwd(), '.eslint-test-temp')
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true })
    }
    tempFile = path.join(tempDir, 'test.tsx')
  })

  afterEach(() => {
    // Clean up temporary files
    if (fs.existsSync(tempFile)) {
      fs.unlinkSync(tempFile)
    }
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true })
    }
  })

  const runESLint = (code: string): { hasError: boolean; output: string; errorCount: number } => {
    fs.writeFileSync(tempFile, code)
    
    try {
      const output = execSync(`npx eslint ${tempFile} --format json`, {
        encoding: 'utf-8',
        cwd: process.cwd()
      })
      
      const results = JSON.parse(output)
      const errorCount = results.reduce((sum: number, result: any) => sum + result.errorCount, 0)
      const hasError = errorCount > 0
      
      return { hasError, output, errorCount }
    } catch (error: any) {
      // ESLint exits with non-zero code when errors are found
      const output = error.stdout || ''
      try {
        const results = JSON.parse(output)
        const errorCount = results.reduce((sum: number, result: any) => sum + result.errorCount, 0)
        return { hasError: true, output, errorCount }
      } catch {
        return { hasError: true, output, errorCount: 1 }
      }
    }
  }

  test('should flag deprecated document.write usage', () => {
    const code = `
      function writeContent() {
        document.write('<div>Hello</div>');
      }
    `
    
    const result = runESLint(code)
    expect(result.hasError).toBe(true)
  })

  test('should flag deprecated attachEvent usage', () => {
    const code = `
      function addListener(element: any, handler: any) {
        element.attachEvent('onclick', handler);
      }
    `
    
    const result = runESLint(code)
    expect(result.hasError).toBe(true)
  })

  test('should not flag modern addEventListener usage', () => {
    const code = `
      function addListener(element: HTMLElement, handler: () => void) {
        element.addEventListener('click', handler);
      }
    `
    
    const result = runESLint(code)
    expect(result.hasError).toBe(false)
  })

  test('should not flag modern event.key usage', () => {
    const code = `
      function handleKeyPress(event: KeyboardEvent) {
        if (event.key === 'Enter') {
          console.log('Enter pressed');
        }
      }
    `
    
    const result = runESLint(code)
    expect(result.hasError).toBe(false)
  })

  test('should not flag modern DOM manipulation', () => {
    const code = `
      function addContent() {
        const div = document.createElement('div');
        div.textContent = 'Hello';
        document.body.appendChild(div);
      }
    `
    
    const result = runESLint(code)
    expect(result.hasError).toBe(false)
  })

  test('should flag deprecated document.execCommand usage', () => {
    const code = `
      function copyText() {
        document.execCommand('copy');
      }
    `
    
    const result = runESLint(code)
    expect(result.hasError).toBe(true)
  })

  test('ESLint configuration includes deprecated API rules', () => {
    // This test validates that our ESLint config has the necessary rules
    const eslintConfigPath = path.join(process.cwd(), 'eslint.config.mjs')
    expect(fs.existsSync(eslintConfigPath)).toBe(true)
    
    const configContent = fs.readFileSync(eslintConfigPath, 'utf-8')
    expect(configContent).toContain('no-restricted-properties')
    expect(configContent).toContain('no-restricted-syntax')
    expect(configContent).toContain('attachEvent')
    expect(configContent).toContain('document.write')
    expect(configContent).toContain('execCommand')
  })
})
