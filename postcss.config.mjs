const config = {
  plugins: {
    "@tailwindcss/postcss": {},
    autoprefixer: {
      overrideBrowserslist: [
        'Chrome >= 80',
        'Firefox >= 78', 
        'Safari >= 13',
        'Edge >= 80',
        'iOS >= 13',
        'Android >= 8'
      ],
      grid: 'autoplace',
      flexbox: 'no-2009'
    }
  },
};

export default config;
