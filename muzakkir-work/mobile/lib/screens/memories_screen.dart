import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/memory_models.dart';
import '../providers/api_providers.dart';

class MemoriesScreen extends ConsumerWidget {
  const MemoriesScreen({super.key, this.onNavigateToSearch});

  final VoidCallback? onNavigateToSearch;

  Future<void> _confirmDelete(
    BuildContext context,
    WidgetRef ref,
    MemoryItem memory,
  ) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete Document Memory'),
        content: Text(
          'Are you sure you want to delete "${memory.originalFilename}"?\n\nThis will remove the file and all associated pgvector chunk embeddings.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.red.shade700),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirmed == true && context.mounted) {
      final success = await deleteMemoryDocument(ref, memory.id);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              success
                  ? 'Deleted "${memory.originalFilename}".'
                  : 'Failed to delete "${memory.originalFilename}".',
            ),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final memoriesAsync = ref.watch(memoriesListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Stored Documents'),
        actions: [
          IconButton(
            tooltip: 'Refresh',
            onPressed: () => ref.invalidate(memoriesListProvider),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: memoriesAsync.when(
        loading: () => const Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 16),
              Text('Loading stored documents from backend…'),
            ],
          ),
        ),
        error: (err, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.cloud_off_rounded, size: 48, color: Colors.red.shade600),
                const SizedBox(height: 16),
                Text(
                  'Failed to fetch memories',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Text(
                  err.toString(),
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                const SizedBox(height: 16),
                FilledButton.icon(
                  onPressed: () => ref.invalidate(memoriesListProvider),
                  icon: const Icon(Icons.refresh),
                  label: const Text('Retry'),
                ),
              ],
            ),
          ),
        ),
        data: (items) {
          if (items.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.folder_open_rounded,
                      size: 64,
                      color: Theme.of(context).colorScheme.outline,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'No Documents in Memory Yet',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Upload PDF, Word, text files or images in the Search tab to build your digital memory knowledge base.',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: Theme.of(context).colorScheme.onSurfaceVariant,
                          ),
                    ),
                    if (onNavigateToSearch != null) ...[
                      const SizedBox(height: 20),
                      FilledButton.icon(
                        onPressed: onNavigateToSearch,
                        icon: const Icon(Icons.upload_file),
                        label: const Text('Go to Upload'),
                      ),
                    ],
                  ],
                ),
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () async => ref.invalidate(memoriesListProvider),
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (context, index) {
                final item = items[index];
                return _MemoryCard(
                  memory: item,
                  onDelete: () => _confirmDelete(context, ref, item),
                );
              },
            ),
          );
        },
      ),
    );
  }
}

class _MemoryCard extends StatelessWidget {
  const _MemoryCard({
    required this.memory,
    required this.onDelete,
  });

  final MemoryItem memory;
  final VoidCallback onDelete;

  Color _getStatusColor() {
    switch (memory.status.toLowerCase()) {
      case 'processed':
        return const Color(0xFF15803D);
      case 'processing':
        return const Color(0xFFD97706);
      case 'failed':
      case 'rejected':
        return const Color(0xFFDC2626);
      default:
        return const Color(0xFF2563EB);
    }
  }

  IconData _getFileIcon() {
    if (memory.isPdf) return Icons.picture_as_pdf;
    if (memory.isImage) return Icons.image_outlined;
    if (memory.isDocx) return Icons.description;
    return Icons.article_outlined;
  }

  Color _getFileColor() {
    if (memory.isPdf) return Colors.red.shade700;
    if (memory.isImage) return Colors.purple.shade700;
    if (memory.isDocx) return Colors.indigo.shade700;
    return Colors.blue.shade700;
  }

  @override
  Widget build(BuildContext context) {
    final statusColor = _getStatusColor();
    final fileColor = _getFileColor();
    final dateStr =
        '${memory.createdAt.year}-${memory.createdAt.month.toString().padLeft(2, '0')}-${memory.createdAt.day.toString().padLeft(2, '0')}';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(_getFileIcon(), color: fileColor, size: 28),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        memory.originalFilename,
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '${memory.fileType.toUpperCase()} • ${memory.formattedFileSize} • Uploaded $dateStr',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Theme.of(context).colorScheme.onSurfaceVariant,
                            ),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  tooltip: 'Delete document',
                  icon: Icon(Icons.delete_outline, color: Colors.red.shade600),
                  onPressed: onDelete,
                ),
              ],
            ),
            const Divider(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                  decoration: BoxDecoration(
                    color: statusColor.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: statusColor.withValues(alpha: 0.3)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        memory.isProcessed
                            ? Icons.check_circle_rounded
                            : (memory.isProcessing
                                ? Icons.sync
                                : Icons.info_outline),
                        size: 14,
                        color: statusColor,
                      ),
                      const SizedBox(width: 6),
                      Text(
                        memory.status.toUpperCase(),
                        style: TextStyle(
                          color: statusColor,
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
                Text(
                  memory.id.length > 8
                      ? 'ID: ${memory.id.substring(0, 8)}…'
                      : 'ID: ${memory.id}',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        fontFamily: 'monospace',
                        color: Theme.of(context).colorScheme.outline,
                      ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
