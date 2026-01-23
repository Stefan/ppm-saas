/**
 * ESLint Rule: no-hardcoded-colors
 * 
 * Prevents direct usage of Tailwind color classes that are not part of the design system.
 * Encourages use of design tokens (primary, neutral, semantic colors).
 * 
 * @type {import('eslint').Rule.RuleModule}
 */

module.exports = {
  meta: {
    type: 'suggestion',
    docs: {
      description: 'Disallow hardcoded Tailwind colors that are not part of the design system',
      category: 'Design System',
      recommended: true,
    },
    fixable: 'code',
    schema: [],
    messages: {
      hardcodedColor: 'Avoid using "{{color}}" directly. Use design tokens instead: primary, neutral, semantic, secondary, accent, success, warning, or error.',
      hardcodedColorWithSuggestion: 'Avoid using "{{color}}" directly. Consider using "{{suggestion}}" from design tokens.',
    },
  },

  create(context) {
    // Design system approved color prefixes
    const approvedColors = new Set([
      'primary',
      'neutral', 
      'semantic',
      'secondary',
      'accent',
      'success',
      'warning',
      'error',
      'inherit',
      'current',
      'transparent',
      'black',
      'white',
    ]);

    // Common Tailwind colors that should be replaced
    const disallowedColors = new Set([
      'slate',
      'gray',
      'zinc',
      'stone',
      'red',
      'orange',
      'amber',
      'yellow',
      'lime',
      'green',
      'emerald',
      'teal',
      'cyan',
      'sky',
      'blue',
      'indigo',
      'violet',
      'purple',
      'fuchsia',
      'pink',
      'rose',
    ]);

    // Mapping suggestions for common colors
    const colorSuggestions = {
      'gray': 'neutral',
      'slate': 'neutral',
      'zinc': 'neutral',
      'stone': 'neutral',
      'blue': 'primary',
      'indigo': 'primary',
      'sky': 'primary',
      'red': 'error',
      'rose': 'error',
      'green': 'success',
      'emerald': 'success',
      'yellow': 'warning',
      'amber': 'warning',
      'orange': 'warning',
    };

    /**
     * Check if a className string contains disallowed colors
     */
    function checkClassNames(node, classNameValue) {
      if (typeof classNameValue !== 'string') return;

      // Match Tailwind color classes: text-blue-500, bg-red-600, border-gray-300, etc.
      const colorClassRegex = /\b(text|bg|border|ring|from|to|via|divide|placeholder|decoration|outline|shadow|accent|caret|fill|stroke)-(\w+)-(\d+)\b/g;
      
      let match;
      while ((match = colorClassRegex.exec(classNameValue)) !== null) {
        const [fullMatch, property, colorName, shade] = match;
        
        if (disallowedColors.has(colorName)) {
          const suggestion = colorSuggestions[colorName];
          
          context.report({
            node,
            messageId: suggestion ? 'hardcodedColorWithSuggestion' : 'hardcodedColor',
            data: {
              color: fullMatch,
              suggestion: suggestion ? `${property}-${suggestion}-${shade}` : '',
            },
            fix: suggestion ? (fixer) => {
              const replacement = classNameValue.replace(
                fullMatch,
                `${property}-${suggestion}-${shade}`
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
