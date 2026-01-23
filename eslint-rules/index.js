/**
 * Custom ESLint Rules for Design System Compliance
 * 
 * These rules enforce the use of design tokens from the ORKA PPM design system.
 */

module.exports = {
  rules: {
    'no-hardcoded-colors': require('./no-hardcoded-colors'),
    'no-hardcoded-spacing': require('./no-hardcoded-spacing'),
  },
};
