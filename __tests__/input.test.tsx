/**
 * @jest-environment jsdom
 * 
 * Unit Tests for Input Component
 * 
 * These tests verify specific examples and edge cases for the Input component.
 * Requirements: 2.5, 2.6
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { Input } from '@/components/ui/input'

describe('Input Component - Unit Tests', () => {
  /**
   * Test: Input rendert mit Label korrekt
   * Requirements: 2.5
   */
  it('should render with label correctly', () => {
    render(<Input label="Email Address" placeholder="Enter email" />)
    
    const label = screen.getByText('Email Address')
    const input = screen.getByPlaceholderText('Enter email')
    
    expect(label).toBeInTheDocument()
    expect(input).toBeInTheDocument()
    
    // Label should have correct styling
    expect(label).toHaveClass('text-sm', 'font-medium', 'text-neutral-700')
  })

  /**
   * Test: Input zeigt Fehlermeldung bei error=true
   * Requirements: 2.5
   */
  it('should show error message when error=true', () => {
    render(
      <Input 
        placeholder="Email" 
        error={true} 
        errorMessage="Invalid email address" 
      />
    )
    
    const errorMessage = screen.getByText('Invalid email address')
    const input = screen.getByPlaceholderText('Email')
    
    expect(errorMessage).toBeInTheDocument()
    expect(errorMessage).toHaveClass('text-error-500')
    expect(input).toHaveClass('border-error-500')
  })

  /**
   * Test: Input akzeptiert alle Standard-HTML-Input-Props
   * Requirements: 2.5
   */
  it('should accept all standard HTML input props', () => {
    const handleChange = jest.fn()
    const handleFocus = jest.fn()
    const handleBlur = jest.fn()
    
    render(
      <Input
        type="email"
        name="email"
        id="email-input"
        value="test@example.com"
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        disabled={false}
        required={true}
        maxLength={100}
        placeholder="Email"
      />
    )
    
    const input = screen.getByPlaceholderText('Email') as HTMLInputElement
    
    expect(input).toHaveAttribute('type', 'email')
    expect(input).toHaveAttribute('name', 'email')
    expect(input).toHaveAttribute('id', 'email-input')
    expect(input).toHaveValue('test@example.com')
    expect(input).toHaveAttribute('required')
    expect(input).toHaveAttribute('maxLength', '100')
    expect(input).not.toBeDisabled()
  })

  /**
   * Test: Input rendert mit allen Größen korrekt
   * Requirements: 2.6
   */
  it('should render with all sizes correctly', () => {
    const { rerender } = render(<Input size="sm" placeholder="Small" />)
    let input = screen.getByPlaceholderText('Small')
    expect(input).toHaveClass('px-3', 'py-1.5', 'text-sm')
    
    rerender(<Input size="md" placeholder="Medium" />)
    input = screen.getByPlaceholderText('Medium')
    expect(input).toHaveClass('px-4', 'py-2', 'text-base')
    
    rerender(<Input size="lg" placeholder="Large" />)
    input = screen.getByPlaceholderText('Large')
    expect(input).toHaveClass('px-5', 'py-3', 'text-lg')
  })

  /**
   * Test: Input without label renders correctly
   */
  it('should render without label when label prop is not provided', () => {
    render(<Input placeholder="No label" />)
    
    const input = screen.getByPlaceholderText('No label')
    const label = screen.queryByText(/./i)
    
    expect(input).toBeInTheDocument()
    // Should not have any label element
    expect(label?.tagName).not.toBe('LABEL')
  })

  /**
   * Test: Input without error message shows only border change
   */
  it('should show only border change when error=true but no errorMessage', () => {
    render(<Input placeholder="Email" error={true} />)
    
    const input = screen.getByPlaceholderText('Email')
    const errorMessage = screen.queryByText(/./i)
    
    expect(input).toHaveClass('border-error-500')
    // Should not have error message paragraph
    expect(errorMessage?.tagName).not.toBe('P')
  })

  /**
   * Test: Input accepts custom className
   */
  it('should accept custom className and merge with default classes', () => {
    render(<Input placeholder="Custom" className="custom-class" />)
    
    const input = screen.getByPlaceholderText('Custom')
    
    expect(input).toHaveClass('custom-class')
    // Should still have base classes
    expect(input).toHaveClass('border', 'rounded-md')
  })

  /**
   * Test: Input disabled state
   */
  it('should render disabled state correctly', () => {
    render(<Input placeholder="Disabled" disabled={true} />)
    
    const input = screen.getByPlaceholderText('Disabled')
    
    expect(input).toBeDisabled()
    expect(input).toHaveClass('disabled:bg-neutral-100', 'disabled:cursor-not-allowed')
  })

  /**
   * Test: Input with label and error message
   */
  it('should render with both label and error message', () => {
    render(
      <Input 
        label="Password"
        placeholder="Enter password"
        error={true}
        errorMessage="Password is too short"
      />
    )
    
    const label = screen.getByText('Password')
    const input = screen.getByPlaceholderText('Enter password')
    const errorMessage = screen.getByText('Password is too short')
    
    expect(label).toBeInTheDocument()
    expect(input).toBeInTheDocument()
    expect(errorMessage).toBeInTheDocument()
    expect(input).toHaveClass('border-error-500')
  })

  /**
   * Test: Input wrapper has full width
   */
  it('should have full width wrapper', () => {
    const { container } = render(<Input placeholder="Full width" />)
    
    const wrapper = container.firstChild as HTMLElement
    
    expect(wrapper).toHaveClass('w-full')
  })

  /**
   * Test: Input has correct base styles
   */
  it('should have correct base styles', () => {
    render(<Input placeholder="Base styles" />)
    
    const input = screen.getByPlaceholderText('Base styles')
    
    expect(input).toHaveClass(
      'w-full',
      'rounded-md',
      'border',
      'bg-white',
      'text-neutral-900',
      'placeholder:text-neutral-500',
      'focus:outline-none',
      'focus:ring-2',
      'focus:ring-primary-500',
      'focus:border-transparent',
      'transition-colors'
    )
  })
})
