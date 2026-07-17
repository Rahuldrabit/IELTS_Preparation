'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, X, FileImage, FileAudio, File as FileIcon, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

// ─────────────────────────────────────────────
//  Types
// ─────────────────────────────────────────────

export interface FileDropZoneProps {
  /** Currently selected files (controlled) */
  files: File[]
  /** Called whenever files are added or removed */
  onFilesChange: (files: File[]) => void
  /** Accepted MIME types / extensions (e.g. 'image/*,.pdf') */
  accept?: string
  /** Maximum number of files allowed */
  maxFiles?: number
  /** Maximum file size in bytes (per file) */
  maxSizeBytes?: number
  /** Label shown in the drop zone */
  label?: string
  /** Subtitle hint */
  hint?: string
  /** Additional className */
  className?: string
}

// ─────────────────────────────────────────────
//  Helpers
// ─────────────────────────────────────────────

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function getFileIcon(file: File) {
  if (file.type.startsWith('image/')) return FileImage
  if (file.type.startsWith('audio/')) return FileAudio
  return FileIcon
}

function isImageFile(file: File): boolean {
  return file.type.startsWith('image/')
}

// ─────────────────────────────────────────────
//  Component
// ─────────────────────────────────────────────

export function FileDropZone({
  files,
  onFilesChange,
  accept = 'image/*,.pdf',
  maxFiles = 10,
  maxSizeBytes = 10 * 1024 * 1024, // 10MB default
  label = 'Drop files here or click to upload',
  hint,
  className,
}: FileDropZoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [previews, setPreviews] = useState<Map<string, string>>(new Map())
  const inputRef = useRef<HTMLInputElement>(null)
  const dragCountRef = useRef(0)

  // Generate image previews
  useEffect(() => {
    const newPreviews = new Map<string, string>()
    const urls: string[] = []

    files.forEach((file) => {
      if (isImageFile(file)) {
        const key = `${file.name}-${file.size}-${file.lastModified}`
        const url = URL.createObjectURL(file)
        newPreviews.set(key, url)
        urls.push(url)
      }
    })

    setPreviews(newPreviews)

    return () => {
      urls.forEach((url) => URL.revokeObjectURL(url))
    }
  }, [files])

  const validateAndAddFiles = useCallback(
    (incoming: File[]) => {
      setError(null)

      // Check max files limit
      const remaining = maxFiles - files.length
      if (remaining <= 0) {
        setError(`Maximum ${maxFiles} files allowed`)
        return
      }

      const toAdd: File[] = []

      for (const file of incoming.slice(0, remaining)) {
        // Size check
        if (file.size > maxSizeBytes) {
          setError(`"${file.name}" exceeds max size of ${formatFileSize(maxSizeBytes)}`)
          continue
        }

        // Duplicate check (by name + size + lastModified)
        const isDuplicate = files.some(
          (f) => f.name === file.name && f.size === file.size && f.lastModified === file.lastModified
        )
        if (isDuplicate) continue

        toAdd.push(file)
      }

      if (toAdd.length > 0) {
        onFilesChange([...files, ...toAdd])
      }

      if (incoming.length > remaining) {
        setError(`Only ${remaining} more file(s) can be added (max ${maxFiles})`)
      }
    },
    [files, maxFiles, maxSizeBytes, onFilesChange]
  )

  const removeFile = useCallback(
    (index: number) => {
      const updated = files.filter((_, i) => i !== index)
      onFilesChange(updated)
      setError(null)
    },
    [files, onFilesChange]
  )

  const clearAll = useCallback(() => {
    onFilesChange([])
    setError(null)
  }, [onFilesChange])

  // ── Drag handlers ──────────────────────────────

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    dragCountRef.current += 1
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    dragCountRef.current -= 1
    if (dragCountRef.current <= 0) {
      setIsDragging(false)
      dragCountRef.current = 0
    }
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragging(false)
      dragCountRef.current = 0

      const droppedFiles = Array.from(e.dataTransfer.files)
      if (droppedFiles.length > 0) {
        validateAndAddFiles(droppedFiles)
      }
    },
    [validateAndAddFiles]
  )

  // ── Input change handler ──────────────────────────────

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        validateAndAddFiles(Array.from(e.target.files))
      }
      // Reset input so same file can be re-selected
      if (inputRef.current) inputRef.current.value = ''
    },
    [validateAndAddFiles]
  )

  const getPreviewUrl = (file: File): string | undefined => {
    const key = `${file.name}-${file.size}-${file.lastModified}`
    return previews.get(key)
  }

  return (
    <div className={cn('space-y-3', className)}>
      {/* Drop zone */}
      <div
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          'relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200',
          isDragging
            ? 'border-primary bg-primary/5 scale-[1.01]'
            : 'border-border hover:border-primary/50 hover:bg-muted/30'
        )}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={accept}
          onChange={handleInputChange}
          className="hidden"
        />

        <div className="flex flex-col items-center gap-2">
          <div
            className={cn(
              'h-14 w-14 rounded-full flex items-center justify-center transition-colors',
              isDragging ? 'bg-primary/20' : 'bg-muted'
            )}
          >
            <Upload
              className={cn(
                'h-7 w-7 transition-colors',
                isDragging ? 'text-primary' : 'text-muted-foreground'
              )}
            />
          </div>
          <p className="text-sm font-medium">
            {isDragging ? 'Drop files here...' : label}
          </p>
          {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
          <p className="text-xs text-muted-foreground">
            {files.length}/{maxFiles} files &middot; Max {formatFileSize(maxSizeBytes)} each
          </p>
        </div>
      </div>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-sm text-destructive"
          >
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* File list */}
      <AnimatePresence mode="popLayout">
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-2"
          >
            {/* Header */}
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium">
                {files.length} file{files.length !== 1 ? 's' : ''} selected
              </h4>
              {files.length > 1 && (
                <Button variant="ghost" size="sm" onClick={clearAll} className="text-xs h-7">
                  Clear all
                </Button>
              )}
            </div>

            {/* File cards */}
            <div className="grid grid-cols-1 gap-2">
              {files.map((file, index) => {
                const Icon = getFileIcon(file)
                const previewUrl = getPreviewUrl(file)

                return (
                  <motion.div
                    key={`${file.name}-${file.size}-${file.lastModified}`}
                    layout
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, x: -20, height: 0 }}
                    transition={{ duration: 0.2 }}
                    className="flex items-center gap-3 p-3 rounded-xl bg-muted/50 border border-border/50 group"
                  >
                    {/* Thumbnail or icon */}
                    {previewUrl ? (
                      <div className="h-10 w-10 rounded-lg overflow-hidden shrink-0 bg-muted">
                        <img
                          src={previewUrl}
                          alt={file.name}
                          className="h-full w-full object-cover"
                        />
                      </div>
                    ) : (
                      <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center shrink-0">
                        <Icon className="h-5 w-5 text-muted-foreground" />
                      </div>
                    )}

                    {/* File info */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{file.name}</p>
                      <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                    </div>

                    {/* Remove button */}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                      onClick={(e) => {
                        e.stopPropagation()
                        removeFile(index)
                      }}
                    >
                      <X className="h-4 w-4" />
                      <span className="sr-only">Remove {file.name}</span>
                    </Button>
                  </motion.div>
                )
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
