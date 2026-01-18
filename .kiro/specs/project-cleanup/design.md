# Design Document: Project Cleanup System

## Overview

The Project Cleanup System is a command-line utility that analyzes, categorizes, and organizes files in the project root directory. It implements a safe, reversible cleanup process that removes temporary files, archives historical documentation, and updates .gitignore to prevent future accumulation.

The system follows a three-phase approach:
1. **Analysis Phase**: Scan and categorize all files
2. **Action Phase**: Archive, delete, or preserve files based on category
3. **Report Phase**: Generate comprehensive summary and update .gitignore

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Cleanup CLI Tool                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   File       │  │   Archive    │  │   Report     │     │
│  │   Scanner    │─▶│   Manager    │─▶│   Generator  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
│         ▼                  ▼                  ▼             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Categorizer  │  │   Deleter    │  │   Gitignore  │     │
│  │              │  │              │  │   Updater    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   File System          │
              │   - Root Directory     │
              │   - Archive Directory  │
              │   - .gitignore         │
              └────────────────────────┘
```

### Component Responsibilities

- **File Scanner**: Reads root directory and identifies all files to process
- **Categorizer**: Applies pattern matching rules to assign files to categories
- **Archive Manager**: Creates archive structure and moves files safely
- **Deleter**: Removes temporary files with verification
- **Report Generator**: Creates summary markdown with statistics
- **Gitignore Updater**: Adds patterns to prevent future accumulation

## Components and Interfaces

### FileScanner

**Purpose**: Scan the root directory and collect file information

**Interface**:
```typescript
interface FileInfo {
  path: string;
  name: string;
  extension: string;
  size: number;
  modifiedTime: Date;
}

class FileScanner {
  scanRootDirectory(): FileInfo[];
  isEssentialFile(filename: string): boolean;
}
```

**Behavior**:
- Reads all files in root directory (non-recursive)
- Excludes directories and hidden files (except .gitignore)
- Collects metadata for each file
- Checks against essential files whitelist

### Categorizer

**Purpose**: Assign each file to a category based on pattern matching

**Interface**:
```typescript
enum FileCategory {
  TEMPORARY_SUMMARY = "temporary_summary",
  TRANSLATION_WORK = "translation_work",
  PERFORMANCE_REPORT = "performance_report",
  TEMPORARY_LOG = "temporary_log",
  ESSENTIAL = "essential",
  SQL_REVIEW = "sql_review",
  UNKNOWN = "unknown"
}

interface CategoryRule {
  category: FileCategory;
  patterns: RegExp[];
  priority: number;
}

class Categorizer {
  categorizeFile(file: FileInfo): FileCategory;
  getCategoryRules(): CategoryRule[];
}
```

**Category Patterns**:

1. **TEMPORARY_SUMMARY**: 
   - `TASK_*_SUMMARY.md`
   - `CHECKPOINT_*_REPORT.md`
   - `FINAL_*_SUMMARY.md`
   - `*_COMPLETION_SUMMARY.md`
   - `*_FIX_SUMMARY.md`

2. **TRANSLATION_WORK**:
   - `BATCH2_*.md`
   - `I18N_*.md` (except I18N_DEVELOPER_GUIDE.md)
   - `WEEK4_*.md`
   - `*_TRANSLATION_*.md`

3. **PERFORMANCE_REPORT**:
   - `DASHBOARD_*.md`
   - `BUNDLE_*.md`
   - `PERFORMANCE_*.md`
   - `OPTIMIZATION_*.md`
   - `LCP_*.md`, `CLS_*.md`, `TBT_*.md`
   - `LIGHTHOUSE_*.md`

4. **TEMPORARY_LOG**:
   - `*.log`
   - `test-results.json`
   - `test-output.log`
   - `bundle-analysis-report.txt`
   - `chrome-scroll-test.html`

5. **ESSENTIAL**:
   - `TESTING_GUIDE.md`
   - `DESIGN_SYSTEM_GUIDE.md`
   - `DEPLOYMENT.md`
   - `AUTH_SETUP_GUIDE.md`
   - `I18N_DEVELOPER_GUIDE.md`
   - All config files (package.json, tsconfig.json, etc.)

6. **SQL_REVIEW**:
   - `*.sql`

**Priority Rules**:
- ESSENTIAL has highest priority (checked first)
- Specific patterns (BATCH2_*) have higher priority than general patterns (*_SUMMARY.md)
- If no pattern matches, category is UNKNOWN

### ArchiveManager

**Purpose**: Create organized archive structure and move files safely

**Interface**:
```typescript
interface ArchiveConfig {
  archiveRoot: string;
  timestamp: string;
}

interface ArchiveResult {
  originalPath: string;
  archivePath: string;
  success: boolean;
}

class ArchiveManager {
  createArchiveStructure(config: ArchiveConfig): void;
  archiveFile(file: FileInfo, category: FileCategory): ArchiveResult;
  generateArchiveIndex(results: ArchiveResult[]): void;
}
```

**Archive Structure**:
```
.kiro/archive/
└── 2024-01-15_cleanup/
    ├── translation-work/
    │   ├── BATCH2_*.md
    │   └── I18N_*.md
    ├── performance-reports/
    │   ├── DASHBOARD_*.md
    │   └── BUNDLE_*.md
    ├── temporary-summaries/
    │   └── TASK_*_SUMMARY.md
    ├── sql-files/
    │   └── *.sql
    └── ARCHIVE_INDEX.md
```

**Behavior**:
- Creates timestamped archive directory
- Organizes files by category in subdirectories
- Preserves file timestamps during move
- Handles name conflicts by appending timestamp
- Generates index file with original locations

### Deleter

**Purpose**: Safely remove temporary files with verification

**Interface**:
```typescript
interface DeletionResult {
  path: string;
  category: FileCategory;
  success: boolean;
  error?: string;
}

class Deleter {
  createDeletionBackup(files: FileInfo[]): void;
  deleteFile(file: FileInfo): DeletionResult;
  verifyDeletion(results: DeletionResult[]): boolean;
}
```

**Safety Checks**:
- Only deletes files in TEMPORARY_SUMMARY and TEMPORARY_LOG categories
- Creates backup list before any deletion
- Verifies file extension is in allowed list (.md, .log, .txt, .json, .html, .csv)
- Skips files that don't match any temporary pattern
- Reports any deletion failures

### ReportGenerator

**Purpose**: Create comprehensive cleanup summary

**Interface**:
```typescript
interface CleanupStats {
  totalFiles: number;
  filesDeleted: number;
  filesArchived: number;
  filesPreserved: number;
  sizeReduced: number;
  archiveLocation: string;
}

class ReportGenerator {
  generateSummary(stats: CleanupStats, results: Map<FileCategory, FileInfo[]>): string;
  writeReport(content: string, outputPath: string): void;
}
```

**Report Contents**:
- Executive summary with statistics
- Files deleted by category
- Files archived with new locations
- Files preserved (essential files)
- Archive directory location
- Before/after file count comparison

### GitignoreUpdater

**Purpose**: Add patterns to prevent future accumulation

**Interface**:
```typescript
class GitignoreUpdater {
  readGitignore(): string[];
  addPatterns(patterns: string[], comment: string): void;
  validateSyntax(): boolean;
  writeGitignore(lines: string[]): void;
}
```

**Patterns to Add**:
```gitignore
# Temporary task summaries and reports
TASK_*_SUMMARY.md
CHECKPOINT_*_REPORT.md
FINAL_*_SUMMARY.md
*_COMPLETION_SUMMARY.md
*_FIX_SUMMARY.md

# Temporary logs and test outputs
*.log
test-results.json
test-output.log
bundle-analysis-report.txt
chrome-scroll-test.html

# Performance investigation files
DASHBOARD_*.md
BUNDLE_*.md
PERFORMANCE_*.md
OPTIMIZATION_*.md
```

## Data Models

### FileInfo
```typescript
interface FileInfo {
  path: string;           // Full path to file
  name: string;           // Filename with extension
  extension: string;      // File extension (.md, .log, etc.)
  size: number;           // File size in bytes
  modifiedTime: Date;     // Last modified timestamp
}
```

### CategoryRule
```typescript
interface CategoryRule {
  category: FileCategory;  // Category to assign
  patterns: RegExp[];      // Regex patterns to match
  priority: number;        // Higher priority checked first
}
```

### CleanupResult
```typescript
interface CleanupResult {
  stats: CleanupStats;
  deletedFiles: Map<FileCategory, FileInfo[]>;
  archivedFiles: Map<FileCategory, ArchiveResult[]>;
  preservedFiles: FileInfo[];
  unknownFiles: FileInfo[];
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Categorization Completeness
*For any* file in the root directory, the categorization function should assign it to exactly one category from the valid set (TEMPORARY_SUMMARY, TRANSLATION_WORK, PERFORMANCE_REPORT, TEMPORARY_LOG, ESSENTIAL, SQL_REVIEW, or UNKNOWN).

**Validates: Requirements 1.1**

### Property 2: Priority-Based Categorization
*For any* file that matches multiple category patterns, the categorization function should assign it to the category with the highest priority, ensuring essential files are never miscategorized.

**Validates: Requirements 1.2, 4.2**

### Property 3: Essential File Preservation
*For any* file in the essential files whitelist, after cleanup completes, the file should remain in its original location with unchanged content and timestamps.

**Validates: Requirements 1.5, 4.5**

### Property 4: Archive Structure Consistency
*For any* set of files to be archived, the archive manager should create a directory structure organized by category with a timestamp, and all archived files should be placed in their corresponding category subdirectory.

**Validates: Requirements 2.1**

### Property 5: Timestamp Preservation During Archiving
*For any* file moved to the archive, its last modified timestamp should be identical before and after the archive operation.

**Validates: Requirements 2.2**

### Property 6: Archive Index Completeness
*For any* cleanup operation, the archive index file should contain entries for all archived files with their original paths and new archive locations.

**Validates: Requirements 2.3, 6.3**

### Property 7: Archive Conflict Resolution
*For any* file being archived where a file with the same name already exists in the archive, the system should append a timestamp to the new file's name to prevent overwrites.

**Validates: Requirements 2.5**

### Property 8: Deletion Safety - Backup Before Delete
*For any* deletion operation, a backup list containing all files to be deleted should be created and persisted before any file is actually removed.

**Validates: Requirements 3.1**

### Property 9: Deletion Safety - Pattern Verification
*For any* file that is deleted, it must match at least one temporary file pattern (TASK_*_SUMMARY.md, *.log, etc.) and have an allowed extension (.md, .log, .txt, .json, .html, .csv).

**Validates: Requirements 3.2, 3.5**

### Property 10: Unknown File Flagging
*For any* file that does not match any known category pattern, the system should flag it in the UNKNOWN category for manual review and should not delete it.

**Validates: Requirements 3.3**

### Property 11: Report Completeness
*For any* cleanup operation, the generated summary report should include: total files processed, files deleted (by category), files archived (with locations), files preserved, archive location, and size reduction statistics.

**Validates: Requirements 3.4, 6.1, 6.2, 6.4, 6.5**

### Property 12: Gitignore Pattern Addition
*For any* cleanup operation, the updated .gitignore file should contain all temporary file patterns with explanatory comments, while preserving all existing entries.

**Validates: Requirements 5.1, 5.3, 5.4**

### Property 13: Gitignore Syntax Validity
*For any* .gitignore update, the resulting file should be syntactically valid according to Git's .gitignore specification.

**Validates: Requirements 5.5**

### Property 14: SQL File Reference Checking
*For any* SQL file in the root directory, the system should check if it is referenced in essential documentation (DEPLOYMENT.md, AUTH_SETUP_GUIDE.md) and preserve it if referenced, or recommend archiving if not referenced.

**Validates: Requirements 7.2, 7.3, 7.4**

### Property 15: SQL Archive Notation
*For any* SQL file that is archived, the cleanup summary report should include its archive location with a note about its manual review status.

**Validates: Requirements 7.1, 7.5**

## Error Handling

### File System Errors

**Scenario**: File cannot be read, moved, or deleted due to permissions or locks

**Handling**:
- Catch file system exceptions for each operation
- Log the error with file path and error message
- Continue processing remaining files
- Include failed operations in the summary report with error details
- Return non-zero exit code if any critical operation fails

### Archive Conflicts

**Scenario**: Archive directory already exists from a previous cleanup

**Handling**:
- Check if archive directory exists before creation
- If exists, append a counter to the timestamp (e.g., `2024-01-15_cleanup_2`)
- Ensure unique archive directory for each run
- Log the conflict resolution in the summary report

### Gitignore Update Failures

**Scenario**: .gitignore file is locked or has syntax errors

**Handling**:
- Validate .gitignore syntax before writing
- Create a backup of original .gitignore before modification
- If write fails, restore from backup
- Log the failure and continue with other cleanup operations
- Include gitignore update status in summary report

### Unknown File Types

**Scenario**: Files that don't match any category pattern

**Handling**:
- Assign to UNKNOWN category
- Do not delete or archive unknown files
- List all unknown files in summary report with recommendation to review manually
- Suggest adding patterns for common unknown file types

### Insufficient Disk Space

**Scenario**: Not enough space to create archive or write reports

**Handling**:
- Check available disk space before starting archive operations
- If insufficient space, abort archive operation and report error
- Suggest deleting temporary files first to free space
- Provide estimate of space needed for archive

## Testing Strategy

### Unit Testing

Unit tests will verify specific examples, edge cases, and error conditions:

**File Scanner Tests**:
- Test scanning empty directory
- Test scanning directory with only essential files
- Test scanning directory with mixed file types
- Test handling of permission errors

**Categorizer Tests**:
- Test each category pattern with example files
- Test priority ordering with files matching multiple patterns
- Test essential files whitelist checking
- Test unknown file handling

**Archive Manager Tests**:
- Test archive directory creation
- Test file moving with timestamp preservation
- Test conflict resolution with duplicate names
- Test index file generation

**Deleter Tests**:
- Test backup list creation
- Test deletion of allowed file types
- Test rejection of disallowed file types
- Test error handling for locked files

**Report Generator Tests**:
- Test report generation with various statistics
- Test markdown formatting
- Test handling of empty results

**Gitignore Updater Tests**:
- Test pattern addition
- Test preservation of existing entries
- Test comment insertion
- Test syntax validation

### Property-Based Testing

Property-based tests will verify universal properties across all inputs using a PBT library (fast-check for TypeScript/JavaScript):

**Configuration**: Each property test will run a minimum of 100 iterations with randomized inputs.

**Test Tagging**: Each test will include a comment referencing the design property:
```typescript
// Feature: project-cleanup, Property 1: Categorization Completeness
```

**Property Test Coverage**:
- Property 1: Generate random file lists and verify each gets exactly one category
- Property 2: Generate files matching multiple patterns and verify priority ordering
- Property 3: Generate random essential files and verify preservation after cleanup
- Property 4: Generate random file sets and verify archive structure consistency
- Property 5: Generate random files and verify timestamp preservation during archiving
- Property 6: Generate random cleanup operations and verify archive index completeness
- Property 7: Generate duplicate file scenarios and verify conflict resolution
- Property 8: Generate random deletion sets and verify backup creation before deletion
- Property 9: Generate random files and verify only pattern-matching files with allowed extensions are deleted
- Property 10: Generate files with unknown patterns and verify flagging behavior
- Property 11: Generate random cleanup operations and verify report completeness
- Property 12: Generate random pattern sets and verify gitignore updates preserve existing entries
- Property 13: Generate random gitignore updates and verify syntax validity
- Property 14: Generate SQL files with and without references and verify preservation logic
- Property 15: Generate SQL archive operations and verify summary notation

**Dual Testing Approach**: Unit tests and property tests are complementary. Unit tests catch specific bugs and edge cases, while property tests verify general correctness across many inputs. Both are necessary for comprehensive coverage.
