import * as fs from 'fs';
import * as path from 'path';
import { FileScanner } from '../FileScanner';

describe('FileScanner', () => {
  const testDir = path.join(__dirname, 'test-data');
  let scanner: FileScanner;

  beforeEach(() => {
    // Create test directory
    if (!fs.existsSync(testDir)) {
      fs.mkdirSync(testDir, { recursive: true });
    }
    scanner = new FileScanner(testDir);
  });

  afterEach(() => {
    // Clean up test directory
    if (fs.existsSync(testDir)) {
      const entries = fs.readdirSync(testDir, { withFileTypes: true });
      for (const entry of entries) {
        const filePath = path.join(testDir, entry.name);
        if (entry.isDirectory()) {
          fs.rmSync(filePath, { recursive: true, force: true });
        } else {
          fs.unlinkSync(filePath);
        }
      }
      fs.rmdirSync(testDir);
    }
  });

  describe('scanRootDirectory', () => {
    it('should scan directory with various file types', () => {
      // Create test files
      fs.writeFileSync(path.join(testDir, 'test.md'), 'content');
      fs.writeFileSync(path.join(testDir, 'test.log'), 'log');
      fs.writeFileSync(path.join(testDir, 'test.json'), '{}');

      const files = scanner.scanRootDirectory();

      expect(files).toHaveLength(3);
      expect(files.map(f => f.name).sort()).toEqual(['test.json', 'test.log', 'test.md']);
      
      files.forEach(file => {
        expect(file.path).toBeTruthy();
        expect(file.name).toBeTruthy();
        expect(file.extension).toBeTruthy();
        expect(file.size).toBeGreaterThanOrEqual(0);
        expect(file.modifiedTime).toBeTruthy();
        expect(typeof file.modifiedTime.getTime()).toBe('number');
      });
    });

    it('should skip directories', () => {
      fs.writeFileSync(path.join(testDir, 'file.md'), 'content');
      fs.mkdirSync(path.join(testDir, 'subdir'));

      const files = scanner.scanRootDirectory();

      expect(files).toHaveLength(1);
      expect(files[0].name).toBe('file.md');
    });

    it('should skip hidden files except allowed ones', () => {
      fs.writeFileSync(path.join(testDir, '.hidden'), 'content');
      fs.writeFileSync(path.join(testDir, '.gitignore'), 'content');
      fs.writeFileSync(path.join(testDir, '.env.local'), 'content');
      fs.writeFileSync(path.join(testDir, 'visible.md'), 'content');

      const files = scanner.scanRootDirectory();

      const names = files.map(f => f.name).sort();
      expect(names).toContain('.gitignore');
      expect(names).toContain('.env.local');
      expect(names).toContain('visible.md');
      expect(names).not.toContain('.hidden');
    });

    it('should handle empty directory', () => {
      const files = scanner.scanRootDirectory();
      expect(files).toHaveLength(0);
    });
  });

  describe('isEssentialFile', () => {
    it('should identify essential documentation files', () => {
      expect(scanner.isEssentialFile('TESTING_GUIDE.md')).toBe(true);
      expect(scanner.isEssentialFile('DESIGN_SYSTEM_GUIDE.md')).toBe(true);
      expect(scanner.isEssentialFile('DEPLOYMENT.md')).toBe(true);
      expect(scanner.isEssentialFile('AUTH_SETUP_GUIDE.md')).toBe(true);
      expect(scanner.isEssentialFile('I18N_DEVELOPER_GUIDE.md')).toBe(true);
    });

    it('should identify essential config files', () => {
      expect(scanner.isEssentialFile('package.json')).toBe(true);
      expect(scanner.isEssentialFile('tsconfig.json')).toBe(true);
      expect(scanner.isEssentialFile('next.config.ts')).toBe(true);
      expect(scanner.isEssentialFile('.gitignore')).toBe(true);
    });

    it('should not identify non-essential files', () => {
      expect(scanner.isEssentialFile('TASK_1_SUMMARY.md')).toBe(false);
      expect(scanner.isEssentialFile('test.log')).toBe(false);
      expect(scanner.isEssentialFile('BUNDLE_ANALYSIS.md')).toBe(false);
    });
  });

  describe('getEssentialFiles', () => {
    it('should return set of essential files', () => {
      const essentialFiles = scanner.getEssentialFiles();
      
      expect(essentialFiles.size).toBeGreaterThan(0);
      expect(essentialFiles.has('TESTING_GUIDE.md')).toBe(true);
      expect(essentialFiles.has('package.json')).toBe(true);
    });
  });
});
