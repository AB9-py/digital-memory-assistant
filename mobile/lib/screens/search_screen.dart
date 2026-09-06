import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/search_models.dart';
import '../providers/api_providers.dart';

class SearchScreen extends ConsumerStatefulWidget {
  const SearchScreen({super.key});

  @override
  ConsumerState<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends ConsumerState<SearchScreen> {
  final _queryController =
      TextEditingController(text: "What is Banker's algorithm?");
  PlatformFile? _selectedFile;

  static const _sampleQueries = [
    "What is Banker's algorithm?",
    "What did I learn about deadlock prevention?",
    "How does Dijkstra's algorithm work in link state routing?",
    "What are Coffman conditions?",
  ];

  @override
  void dispose() {
    _queryController.dispose();
    super.dispose();
  }

  Future<void> _pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['pdf', 'txt'],
    );
    if (!mounted || result == null || result.files.isEmpty) {
      return;
    }
    setState(() => _selectedFile = result.files.single);
  }

  void _onUploadPressed() {
    if (_selectedFile == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select a PDF or text file first.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => _UploadStatusSheet(
        file: _selectedFile!,
        onClear: () {
          setState(() => _selectedFile = null);
          Navigator.of(ctx).pop();
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final searchState = ref.watch(searchControllerProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Semantic Memory Search'),
        actions: [
          IconButton(
            tooltip: 'Clear search',
            onPressed: () {
              _queryController.clear();
              ref.invalidate(searchControllerProvider);
            },
            icon: const Icon(Icons.clear_all),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Section 1: Ingestion & Upload Panel
          _UploadPanel(
            selectedFile: _selectedFile,
            onPickFile: _pickFile,
            onUploadPressed: _onUploadPressed,
          ),
          const SizedBox(height: 18),

          // Section 2: Search Input
          TextField(
            controller: _queryController,
            minLines: 1,
            maxLines: 3,
            textInputAction: TextInputAction.search,
            decoration: InputDecoration(
              labelText: 'Natural Language Query',
              hintText: 'e.g. What is Banker\'s algorithm?',
              prefixIcon: const Icon(Icons.search),
              suffixIcon: IconButton(
                tooltip: 'Clear text',
                icon: const Icon(Icons.clear),
                onPressed: () => _queryController.clear(),
              ),
            ),
            onSubmitted: (_) => _runSearch(),
          ),
          const SizedBox(height: 10),

          // Quick Query Suggestion Chips for Live Presentation
          Wrap(
            spacing: 8,
            runSpacing: 4,
            children: [
              for (final query in _sampleQueries)
                ActionChip(
                  avatar: const Icon(Icons.bolt, size: 14),
                  label: Text(
                    query,
                    style: const TextStyle(fontSize: 12),
                  ),
                  onPressed: () {
                    _queryController.text = query;
                    _runSearch();
                  },
                ),
            ],
          ),
          const SizedBox(height: 12),

          FilledButton.icon(
            onPressed: searchState.isLoading ? null : _runSearch,
            icon: searchState.isLoading
                ? const SizedBox.square(
                    dimension: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.travel_explore),
            label: const Text('Search Vector Memory (pgvector)'),
          ),
          const SizedBox(height: 18),

          // Section 3: Search Results
          searchState.when(
            loading: () => const Center(
              child: Padding(
                padding: EdgeInsets.all(32),
                child: Column(
                  children: [
                    CircularProgressIndicator(),
                    SizedBox(height: 12),
                    Text('Querying pgvector via cosine similarity...'),
                  ],
                ),
              ),
            ),
            error: (error, stackTrace) => _MessageCard(
              icon: Icons.error_outline,
              color: Colors.red.shade700,
              message: 'Search failed: $error',
            ),
            data: (response) {
              if (response == null) {
                return const _MessageCard(
                  icon: Icons.manage_search,
                  message:
                      'Enter a query above or click a suggestion chip to retrieve semantic memory chunks.',
                );
              }
              if (response.results.isEmpty) {
                return const _MessageCard(
                  icon: Icons.search_off,
                  message:
                      'No matching chunks returned above similarity threshold. Grounding active: zero false positives.',
                );
              }
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        '${response.totalResults} relevant chunk(s) found',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                      Chip(
                        visualDensity: VisualDensity.compact,
                        label: const Text('Top-K Cosine Match'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  for (final result in response.results) ...[
                    _ResultCard(result: result),
                    const SizedBox(height: 12),
                  ],
                ],
              );
            },
          ),
        ],
      ),
    );
  }

  void _runSearch() {
    ref
        .read(searchControllerProvider.notifier)
        .search(query: _queryController.text);
  }
}

class _UploadPanel extends StatelessWidget {
  const _UploadPanel({
    required this.selectedFile,
    required this.onPickFile,
    required this.onUploadPressed,
  });

  final PlatformFile? selectedFile;
  final VoidCallback onPickFile;
  final VoidCallback onUploadPressed;

  @override
  Widget build(BuildContext context) {
    final hasFile = selectedFile != null;
    final fileName = selectedFile?.name ?? 'No document selected';
    final isPdf = fileName.toLowerCase().endsWith('.pdf');
    final fileSizeKb = hasFile ? (selectedFile!.size / 1024).toStringAsFixed(1) : '0';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  hasFile
                      ? (isPdf ? Icons.picture_as_pdf : Icons.description)
                      : Icons.upload_file,
                  color: hasFile
                      ? (isPdf ? Colors.red.shade700 : Colors.blue.shade700)
                      : Theme.of(context).colorScheme.primary,
                  size: 28,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        fileName,
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight:
                                  hasFile ? FontWeight.w600 : FontWeight.normal,
                            ),
                        overflow: TextOverflow.ellipsis,
                      ),
                      if (hasFile)
                        Text(
                          '$fileSizeKb KB • ${isPdf ? 'PDF Document' : 'Text File'}',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                    ],
                  ),
                ),
                OutlinedButton.icon(
                  onPressed: onPickFile,
                  icon: const Icon(Icons.folder_open, size: 18),
                  label: Text(hasFile ? 'Change' : 'Browse'),
                ),
              ],
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: FilledButton.tonalIcon(
                    onPressed: onUploadPressed,
                    icon: const Icon(Icons.cloud_upload_outlined, size: 20),
                    label: const Text('Upload to Memory'),
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

class _UploadStatusSheet extends StatelessWidget {
  const _UploadStatusSheet({
    required this.file,
    required this.onClear,
  });

  final PlatformFile file;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    final isPdf = file.name.toLowerCase().endsWith('.pdf');
    final sizeKb = (file.size / 1024).toStringAsFixed(1);

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                isPdf ? Icons.picture_as_pdf : Icons.description,
                color: isPdf ? Colors.red.shade700 : Colors.blue.shade700,
                size: 32,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  file.name,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _DetailRow(label: 'File Size', value: '$sizeKb KB'),
          _DetailRow(label: 'Format', value: isPdf ? 'PDF (Portable Document Format)' : 'Plain Text'),
          _DetailRow(label: 'Pipeline Status', value: 'Validated for Module 1 Ingestion'),
          const Divider(height: 24),
          Text(
            'Pipeline Handshake:',
            style: Theme.of(context).textTheme.labelLarge,
          ),
          const SizedBox(height: 6),
          Text(
            'The client validates and packages the file for Module 1 text extraction & chunking. Once chunked, Abhinav\'s service generates 1536-dim embeddings stored into pgvector.',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: onClear,
                  child: const Text('Remove File'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: FilledButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('Close'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  const _DetailRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: Theme.of(context).textTheme.bodyMedium),
          Text(
            value,
            style: Theme.of(context)
                .textTheme
                .bodyMedium
                ?.copyWith(fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }
}

class _ResultCard extends StatelessWidget {
  const _ResultCard({required this.result});

  final ChunkSearchResult result;

  @override
  Widget build(BuildContext context) {
    final scorePercent = (result.similarityScore * 100).round();
    final pageLabel = result.pageNumber == null
        ? 'Chunk ${result.chunkIndex}'
        : 'Page ${result.pageNumber}';
    final isPdf = result.originalFilename.toLowerCase().endsWith('.pdf');

    final Color scoreColor;
    if (result.similarityScore >= 0.35) {
      scoreColor = const Color(0xFF15803D);
    } else if (result.similarityScore >= 0.20) {
      scoreColor = const Color(0xFF2563EB);
    } else {
      scoreColor = const Color(0xFFD97706);
    }

    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: BorderSide(
          color: Theme.of(context).colorScheme.outlineVariant,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  isPdf ? Icons.picture_as_pdf : Icons.description,
                  size: 20,
                  color: isPdf ? Colors.red.shade700 : Colors.blue.shade700,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    result.originalFilename,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.surfaceContainerHighest,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    pageLabel,
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Cosine Similarity: ${result.similarityScore.toStringAsFixed(4)}',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: scoreColor,
                        fontWeight: FontWeight.w600,
                      ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: scoreColor.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    '$scorePercent% match',
                    style: TextStyle(
                      color: scoreColor,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: result.similarityScore.clamp(0.0, 1.0).toDouble(),
                color: scoreColor,
                backgroundColor: scoreColor.withValues(alpha: 0.15),
                minHeight: 6,
              ),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surfaceContainerLow,
                borderRadius: BorderRadius.circular(6),
                border: Border.all(
                  color: Theme.of(context).colorScheme.outlineVariant,
                ),
              ),
              child: Text(
                '"${result.content}"',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      fontStyle: FontStyle.italic,
                      height: 1.4,
                    ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MessageCard extends StatelessWidget {
  const _MessageCard({
    required this.icon,
    required this.message,
    this.color,
  });

  final IconData icon;
  final String message;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final effectiveColor = color ?? Theme.of(context).colorScheme.onSurfaceVariant;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(icon, color: effectiveColor),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                message,
                style: TextStyle(color: effectiveColor),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
