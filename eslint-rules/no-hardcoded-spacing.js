/**
 * ESLint Rule: no-hardcoded-spacing
 * 
 * Prevents direct usage of arbitrary spacing values in Tailwind classes.
 * Encourages use of design token spacing scale (0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16).
 * 
 * @type {import('eslint').Rule.RuleModule}
 */

module.exports = {
  meta: {
    type: 'suggestion',
    docs: {
      description: 'Disallow hardcoded spacing values that are not part of the design system',
      category: 'Design System',
      recommended: true,
    },
    fixable: 'code',
    schema: [],
    messages: {
      hardcodedSpacing: 'Avoid using "{{spacing}}" directly. Use design token spacing: 0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16, touch-target, touch-target-comfortable, or touch-target-large.',
      arbitrarySpacing: 'Avoid using arbitrary spacing value "{{spacing}}". Use design token spacing instead.',
      hardcodedSpacingWithSuggestion: 'Avoid using "{{spacing}}" directly. Consider using "{{suggestion}}" from design tokens.',
    },
  },

  create(context) {
    // Design system approved spacing values
    const approvedSpacing = new Set([
      '0', '1', '2', '3', '4', '5', '6', '8', '10', '12', '16',
      'touch-target', 'touch-target-comfortable', 'touch-target-large',
      'px', 'auto', 'full', 'screen',
    ]);

    // Common spacing values that should be replaced
    const spacingSuggestions = {
      '7': '6',   // 28px -> 24px
      '9': '8',   // 36px -> 32px
      '11': '12', // 44px -> 48px
      '14': '16', // 56px -> 64px
      '15': '16', // 60px -> 64px
      '20': '16', // 80px -> 64px
      '24': '16', // 96px -> 64px
      '32': '16', // 128px -> 64px
    };

    /**
     * Check if a className string contains disallowed spacing
     */
    function checkClassNames(node, classNameValue) {
      if (typeof classNameValue !== 'string') return;

      // Match Tailwind spacing classes: p-7, m-14, gap-9, space-x-11, etc.
      // Also match arbitrary values: p-[20px], m-[1.5rem], etc.
      const spacingClassRegex = /\b(p|px|py|pt|pb|pl|pr|m|mx|my|mt|mb|ml|mr|gap|space-x|space-y|inset|top|right|bottom|left|w|h|min-w|min-h|max-w|max-h)-(\[[\w.]+(?:px|rem|em|%|vh|vw)?\]|\d+(?:\.\d+)?)\b/g;
      
      let match;
      while ((match = spacingClassRegex.exec(classNameValue)) !== null) {
        const [fullMatch, property, value] = match;
        
        // Check for arbitrary values (e.g., p-[20px])
        if (value.startsWith('[') && value.endsWith(']')) {
          context.report({
            node,
            messageId: 'arbitrarySpacing',
            data: {
              spacing: fullMatch,
            },
          });
          continue;
        }
        
        // Check if spacing value is not in approved list
        if (!approvedSpacing.has(value)) {
          const suggestion = spacingSuggestions[value];
          
          context.report({
            node,
            messageId: suggestion ? 'hardcodedSpacingWithSuggestion' : 'hardcodedSpacing',
            data: {
              spacing: fullMatch,
              suggestion: suggestion ? `${property}-${suggestion}` : '',
            },
            fix: suggestion ? (fixer) => {
              const replacement = classNameValue.replace(
                fullMatch,
                `${property}-${suggestion}`
              );
              return fixer.replaceText(node, `"${replacement}"`);
            } : null,
          });
        }
      }
    }

    return {
      // Check JSX className attributes
      JSXAttribute(node) {
        if (node.name.name === 'className' && node.value) {
          if (node.value.type === 'Literal') {
            checkClassNames(node.value, node.value.value);
          } else if (node.value.type === 'JSXExpressionContainer') {
            const expr = node.value.expression;
            
            // Handle template literals
            if (expr.type === 'TemplateLiteral') {
              expr.quasis.forEach(quasi => {
                checkClassNames(quasi, quasi.value.raw);
              });
            }
            
            // Handle string literals
            if (expr.type === 'Literal' && typeof expr.value === 'string') {
              checkClassNames(expr, expr.value);
            }
          }
        }
      },

      // Check class property in objects (for cn() calls, etc.)
      Property(node) {
        if (
          (node.key.name === 'className' || node.key.name === 'class') &&
          node.value.type === 'Literal' &&
          typeof node.value.value === 'string'
        ) {
          checkClassNames(node.value, node.value.value);
        }
      },
    };
  },
};
