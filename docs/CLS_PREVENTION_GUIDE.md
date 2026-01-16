# CLS Prevention Developer Guide

## Quick Reference

### ✅ DO: Use CLS-Safe Components

```tsx
import { CLSSafeContainer, CLSSafeImage, CLSSafeFixed } from '@/components/ui/CLSSafeContainer'

// Reserve space for dynamic content
<CLSSafeContainer minHeight="200px">
  {loading ? <Skeleton /> : <Content />}
</CLSSafeContainer>

// Images with guaranteed aspect ratio
<CLSSafeImage 
  src="/image.jpg" 
  alt="Description"
  width={800}
  height={600}
/>

// Fixed positioned elements
<CLSSafeFixed position="top-right">
  <NotificationBadge />
</CLSSafeFixed>
```

### ✅ DO: Always Specify Image Dimensions

```tsx
// Good - prevents layout shift
<img 
  src="/hero.jpg" 
  width={1920} 
  height={1080} 
  alt="Hero image"
/>

// Also good - using aspect ratio
<img 
  src="/hero.jpg" 
  style={{ aspectRatio: '16 / 9' }}
  alt="Hero image"
/>
```

### ❌ DON'T: Images Without Dimensions

```tsx
// Bad - causes layout shift when image loads
<img src="/hero.jpg" alt="Hero image" />
```

### ✅ DO: Use Skeleton Loaders with Fixed Heights

```tsx
import { SkeletonCard } from '@/components/ui/skeletons/SkeletonCard'

// Good - skeleton has same height as content
{loading ? (
  <SkeletonCard variant="stat" />
) : (
  <StatCard data={data} />
)}
```

### ❌ DON'T: Empty Loading States

```tsx
// Bad - content appears suddenly causing shift
{loading ? null : <StatCard data={data} />}

// Bad - loading spinner without space reservation
{loading ? <Spinner /> : <StatCard data={data} />}
```

### ✅ DO: Reserve Space for Dynamic Content

```tsx
// Good - minimum height prevents shift
<div style={{ minHeight: '400px' }}>
  {data.map(item => <Card key={item.id} {...item} />)}
</div>
```

### ✅ DO: Use CSS Containment

```tsx
// Good - isolates component from parent layout
<div style={{ contain: 'layout style paint' }}>
  <DynamicComponent />
</div>
```

### ✅ DO: Use Transform for Animations

```css
/* Good - doesn't affect layout */
.slide-in {
  transform: translateX(100px);
  transition: transform 0.3s;
}
```

### ❌ DON'T: Use Layout-Affecting Properties for Animations

```css
/* Bad - causes layout recalculation */
.slide-in {
  margin-left: 100px;
  transition: margin-left 0.3s;
}
```

### ✅ DO: Optimize Font Loading

```typescript
// Good - prevents FOUT
import { Inter } from 'next/font/google'

const inter = Inter({ 
  display: 'optional', // or 'swap' with fallback
  subsets: ['latin']
})
```

### ✅ DO: Use Lazy Loading with Suspense

```tsx
import { lazy, Suspense } from 'react'

const HeavyComponent = lazy(() => import('./HeavyComponent'))

// Good - skeleton reserves space
<Suspense fallback={<SkeletonCard variant="project" />}>
  <HeavyComponent />
</Suspense>
```

### ❌ DON'T: Lazy Load Without Fallback

```tsx
// Bad - no space reservation during load
<Suspense fallback={null}>
  <HeavyComponent />
</Suspense>
```

## Common Patterns

### Pattern 1: Dashboard Cards

```tsx
function DashboardCard({ loading, data }) {
  return (
    <CLSSafeContainer 
      minHeight="120px"
      className="bg-white p-6 rounded-lg shadow"
    >
      {loading ? (
        <SkeletonCard variant="stat" />
      ) : (
        <div>
          <h3>{data.title}</h3>
          <p className="text-3xl">{data.value}</p>
        </div>
      )}
    </CLSSafeContainer>
  )
}
```

### Pattern 2: Image Galleries

```tsx
function ImageGallery({ images }) {
  return (
    <div className="grid grid-cols-3 gap-4">
      {images.map(img => (
        <CLSSafeImage
          key={img.id}
          src={img.url}
          alt={img.alt}
          width={400}
          height={300}
          aspectRatio="4 / 3"
        />
      ))}
    </div>
  )
}
```

### Pattern 3: Modal Dialogs

```tsx
function Modal({ isOpen, children }) {
  return (
    <div 
      className={`fixed inset-0 ${isOpen ? 'block' : 'hidden'}`}
      style={{
        contain: 'layout style paint',
        willChange: 'transform',
        transform: 'translateZ(0)'
      }}
    >
      {children}
    </div>
  )
}
```

### Pattern 4: Dynamic Lists

```tsx
function ProjectList({ projects, loading }) {
  return (
    <div style={{ minHeight: '400px', contain: 'layout' }}>
      {loading ? (
        Array.from({ length: 5 }).map((_, i) => (
          <SkeletonCard key={i} variant="project" />
        ))
      ) : (
        projects.map(project => (
          <ProjectCard key={project.id} {...project} />
        ))
      )}
    </div>
  )
}
```

## Debugging CLS Issues

### 1. Chrome DevTools Performance Tab

1. Open DevTools (F12)
2. Go to Performance tab
3. Click Record
4. Reload page and interact
5. Stop recording
6. Look for red "Layout Shift" bars in the Experience lane
7. Click on them to see which elements shifted

### 2. Lighthouse Audit

1. Open DevTools (F12)
2. Go to Lighthouse tab
3. Select "Performance" category
4. Click "Analyze page load"
5. Check CLS score in Core Web Vitals
6. Review "Avoid large layout shifts" section

### 3. Layout Shift Regions

Enable in Chrome DevTools:
1. Open DevTools
2. Press Cmd+Shift+P (Mac) or Ctrl+Shift+P (Windows)
3. Type "Show Rendering"
4. Check "Layout Shift Regions"
5. Reload page - shifted areas will flash blue

### 4. Console Logging

The CLS prevention system logs shifts in development:

```javascript
// Check console for:
Layout shift detected: {
  value: 0.05,
  sources: [...],
  timestamp: 1234.56
}
```

## Checklist for New Components

- [ ] Images have width/height or aspect-ratio
- [ ] Loading states use skeleton loaders with fixed dimensions
- [ ] Dynamic content has min-height reservation
- [ ] Fixed/absolute positioned elements use CSS containment
- [ ] Animations use transform instead of layout properties
- [ ] Fonts use display: optional or swap with fallback
- [ ] Lazy-loaded components have proper Suspense fallbacks
- [ ] Modals/overlays use CSS containment
- [ ] No content injected above the fold after initial render

## Testing Your Changes

```bash
# Run CLS prevention tests
npm test -- __tests__/cls-prevention.test.ts

# Run full test suite
npm test

# Check for TypeScript errors
npm run type-check

# Build and check for issues
npm run build
```

## Resources

- [Web.dev CLS Guide](https://web.dev/cls/)
- [CSS Containment](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Containment)
- [Optimize Cumulative Layout Shift](https://web.dev/optimize-cls/)
- [Debug Layout Shifts](https://web.dev/debug-layout-shifts/)

## Questions?

If you're unsure whether your component might cause CLS:
1. Test it with Chrome DevTools Performance tab
2. Check the console for layout shift warnings
3. Use the Layout Shift Regions visualization
4. Ask for a code review focusing on CLS prevention
