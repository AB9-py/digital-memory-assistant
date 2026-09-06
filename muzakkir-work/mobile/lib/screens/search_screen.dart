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
  final _queryController = TextEditingController(text: 'What is deadlock prevention?');
  PlatformFile? _selectedFile;

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

  @override
  Widget build(BuildContext context) {
    final searchState = ref.watch(searchControllerProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Memory Search')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _UploadPanel(
            selectedFile: _selectedFile,
            onPickFile: _pickFile,
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _queryController,
            minLines: 1,
            maxLines: 3,
            textInputAction: TextInputAction.search,
            decoration: const InputDecoration(
              labelText: 'Search memories',
              prefixIcon: Icon(Icons.search),
            ),
            onSubmitted: (_) => _runSearch(),
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
            label: const Text('Search Memories'),
          ),
          const SizedBox(height: 16),
          searchState.when(
            loading: () => const SizedBox.shrink(),
            error: (error, stackTrace) => _MessageCard(
              icon: Icons.error_outline,
              message: error.toString(),
            ),
            data: (response) {
              if (response == null) {
                return const _MessageCard(
                  icon: Icons.manage_search,
                  message: 'Run a search to view retrieved memory chunks.',
                );
              }
              if (response.results.isEmpty) {
                return const _MessageCard(
                  icon: Icons.search_off,
                  message: 'No matching chunks returned for this query.',
                );
              }
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${response.totalResults} result(s)',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
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
  });

  final PlatformFile? selectedFile;
  final VoidCallback onPickFile;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.upload_file),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    selectedFile?.name ?? 'Choose a PDF or text file',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                IconButton(
                  tooltip: 'Pick file',
                  onPressed: onPickFile,
                  icon: const Icon(Icons.folder_open),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'File upload is waiting on a backend multipart endpoint.',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
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

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    result.originalFilename,
                    style: Theme.of(context).textTheme.titleMedium,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(width: 8),
                Chip(
                  visualDensity: VisualDensity.compact,
                  label: Text(pageLabel),
                ),
              ],
            ),
            const SizedBox(height: 12),
            LinearProgressIndicator(
              value: result.similarityScore.clamp(0.0, 1.0).toDouble(),
            ),
            const SizedBox(height: 6),
            Text('$scorePercent% match'),
            const SizedBox(height: 12),
            Text(result.content),
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
  });

  final IconData icon;
  final String message;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(icon),
            const SizedBox(width: 12),
            Expanded(child: Text(message)),
          ],
        ),
      ),
    );
  }
}
