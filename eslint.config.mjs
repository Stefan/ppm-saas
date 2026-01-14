import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    languageOptions: {
      globals: {
        // Jest globals
        jest: "readonly",
        describe: "readonly",
        it: "readonly",
        test: "readonly",
        expect: "readonly",
        beforeEach: "readonly",
        afterEach: "readonly",
        beforeAll: "readonly",
        afterAll: "readonly",
        // Node.js globals
        global: "readonly",
        process: "readonly",
        Buffer: "readonly",
        NodeJS: "readonly",
        // Browser globals
        window: "readonly",
        document: "readonly",
        navigator: "readonly",
        console: "readonly",
        // Browser API types
        IDBTransactionMode: "readonly",
        IDBObjectStoreParameters: "readonly",
        IDBIndexParameters: "readonly",
        RequestInit: "readonly",
        NotificationPermission: "readonly",
        NotificationOptions: "readonly",
        BufferSource: "readonly",
        IntersectionObserverInit: "readonly",
        // React globals
        React: "readonly",
        JSX: "readonly"
      }
    },
    rules: {
      // Deprecated API avoidance rules
      "no-restricted-globals": [
        "error",
        {
          name: "event",
          message: "Use the event parameter passed to the handler instead of the global 'event' object."
        }
      ],
      "no-restricted-properties": [
        "error",
        // Deprecated event properties
        {
          object: "event",
          property: "keyCode",
          message: "event.keyCode is deprecated. Use event.key or event.code instead."
        },
        {
          object: "event",
          property: "which",
          message: "event.which is deprecated. Use event.key or event.code instead."
        },
        {
          object: "event",
          property: "charCode",
          message: "event.charCode is deprecated. Use event.key instead."
        },
        {
          object: "event",
          property: "returnValue",
          message: "event.returnValue is deprecated. Use event.preventDefault() instead."
        },
        {
          object: "event",
          property: "srcElement",
          message: "event.srcElement is deprecated. Use event.target instead."
        },
        // Deprecated document methods
        {
          object: "document",
          property: "write",
          message: "document.write is deprecated. Use DOM manipulation methods like appendChild() instead."
        },
        {
          object: "document",
          property: "writeln",
          message: "document.writeln is deprecated. Use DOM manipulation methods like appendChild() instead."
        },
        {
          object: "document",
          property: "clear",
          message: "document.clear is deprecated. Use modern DOM manipulation instead."
        },
        {
          object: "document",
          property: "captureEvents",
          message: "document.captureEvents is deprecated. Use addEventListener with capture option instead."
        },
        {
          object: "document",
          property: "releaseEvents",
          message: "document.releaseEvents is deprecated. Use removeEventListener instead."
        },
        // Deprecated window methods
        {
          object: "window",
          property: "showModalDialog",
          message: "window.showModalDialog is deprecated. Use the <dialog> element or a custom modal instead."
        },
        {
          object: "window",
          property: "createPopup",
          message: "window.createPopup is deprecated. Use modern popup/modal patterns instead."
        },
        // Deprecated execCommand
        {
          object: "document",
          property: "execCommand",
          message: "document.execCommand is deprecated. Use the Clipboard API or modern contenteditable APIs instead."
        },
        {
          object: "document",
          property: "queryCommandEnabled",
          message: "document.queryCommandEnabled is deprecated. Use modern contenteditable APIs instead."
        },
        {
          object: "document",
          property: "queryCommandState",
          message: "document.queryCommandState is deprecated. Use modern contenteditable APIs instead."
        },
        {
          object: "document",
          property: "queryCommandSupported",
          message: "document.queryCommandSupported is deprecated. Use modern contenteditable APIs instead."
        }
      ],
      "no-restricted-syntax": [
        "error",
        // Deprecated event handling
        {
          selector: "CallExpression[callee.property.name='attachEvent']",
          message: "attachEvent is deprecated. Use addEventListener instead."
        },
        {
          selector: "CallExpression[callee.property.name='detachEvent']",
          message: "detachEvent is deprecated. Use removeEventListener instead."
        },
        {
          selector: "CallExpression[callee.property.name='createEvent']",
          message: "createEvent is deprecated. Use new Event() or new CustomEvent() instead."
        },
        {
          selector: "CallExpression[callee.property.name='initEvent']",
          message: "initEvent is deprecated. Use the Event constructor with options instead."
        },
        {
          selector: "CallExpression[callee.property.name='initMouseEvent']",
          message: "initMouseEvent is deprecated. Use the MouseEvent constructor instead."
        },
        {
          selector: "CallExpression[callee.property.name='initKeyboardEvent']",
          message: "initKeyboardEvent is deprecated. Use the KeyboardEvent constructor instead."
        }
      ],
      
      // Catch common JSX syntax issues
      "react/jsx-no-undef": "error",
      "react/jsx-uses-react": "error",
      "react/jsx-uses-vars": "error",
      "react/jsx-closing-bracket-location": "error",
      "react/jsx-closing-tag-location": "error",
      "react/jsx-curly-spacing": ["error", "never"],
      "react/jsx-equals-spacing": ["error", "never"],
      "react/jsx-no-duplicate-props": "error",
      "react/jsx-props-no-multi-spaces": "error",
      "react/jsx-tag-spacing": "error",
      
      // Catch common JavaScript syntax issues
      "no-undef": "error",
      "no-unused-vars": "warn",
      "no-unreachable": "error",
      "no-dupe-keys": "error",
      "no-duplicate-case": "error",
      "no-empty": "error",
      "no-extra-semi": "error",
      "no-func-assign": "error",
      "no-invalid-regexp": "error",
      "no-irregular-whitespace": "error",
      "no-obj-calls": "error",
      "no-sparse-arrays": "error",
      "no-unexpected-multiline": "error",
      "use-isnan": "error",
      "valid-typeof": "error",
      
      // TypeScript specific
      "@typescript-eslint/no-unused-vars": "warn",
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-non-null-assertion": "warn",
      
      // Import/Export issues
      "import/no-unresolved": "off", // Next.js handles this
      "import/named": "error",
      "import/default": "error",
      "import/namespace": "error",
      "import/no-duplicates": "error",
      
      // Potential runtime errors
      "array-callback-return": "error",
      "no-constructor-return": "error",
      "no-promise-executor-return": "error",
      "no-self-compare": "error",
      "no-template-curly-in-string": "error",
      "no-unmodified-loop-condition": "error",
      "no-useless-backreference": "error",
      "require-atomic-updates": "error"
    }
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    "scripts/**", // Ignore our validation scripts
  ]),
]);

export default eslintConfig;
