/**
 * Core types for the Project Cleanup System
 */

/**
 * Information about a file in the root directory
 */
export interface FileInfo {
  path: string;           // Full path to file
  name: string;           // Filename with extension
  extension: string;      // File extension (.md, .log, etc.)
  size: number;           // File size in bytes
  modifiedTime: Date;     // Last modified timestamp
}

/**
 * Categories for file classification
 */
export enum FileCategory {
  TEMPORARY_SUMMARY = "temporary_summary",
  TRANSLATION_WORK = "translation_work",
  PERFORMANCE_REPORT = "performance_report",
  TEMPORARY_LOG = "temporary_log",
  ESSENTIAL = "essential",
  SQL_REVIEW = "sql_review",
  UNKNOWN = "unknown"
}

/**
 * Rule for categorizing files
 */
export interface CategoryRule {
  category: FileCategory;  // Category to assign
  patterns: RegExp[];      // Regex patterns to match
  priority: number;        // Higher priority checked first
}

/**
 * Configuration for archive creation
 */
export interface ArchiveConfig {
  archiveRoot: string;     // Root directory for archives
  timestamp: string;       // Timestamp for this archive
}

/**
 * Result of archiving a single file
 */
export interface ArchiveResult {
  originalPath: string;    // Original file location
  archivePath: string;     // New location in archive
  success: boolean;        // Whether operation succeeded
  error?: string;          // Error message if failed
}

/**
 * Result of deleting a single file
 */
export interface DeletionResult {
  path: string;            // Path to deleted file
  category: FileCategory;  // Category of deleted file
  success: boolean;        // Whether operation succeeded
  error?: string;          // Error message if failed
}

/**
 * Statistics about the cleanup operation
 */
export interface CleanupStats {
  totalFiles: number;      // Total files processed
  filesDeleted: number;    // Number of files deleted
  filesArchived: number;   // Number of files archived
  filesPreserved: number;  // Number of files preserved
  sizeReduced: number;     // Total size reduction in bytes
  archiveLocation: string; // Path to archive directory
}

/**
 * Complete result of cleanup operation
 */
export interface CleanupResult {
  stats: CleanupStats;
  deletedFiles: Map<FileCategory, FileInfo[]>;
  archivedFiles: Map<FileCategory, ArchiveResult[]>;
  preservedFiles: FileInfo[];
  unknownFiles: FileInfo[];
}
