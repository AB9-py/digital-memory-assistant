import 'package:digital_memory_assistant/models/health_status.dart';
import 'package:digital_memory_assistant/models/memory_models.dart';
import 'package:digital_memory_assistant/models/search_models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('HealthStatus Model Tests', () {
    test('parses fully healthy status response with latency', () {
      final status = HealthStatus.fromJson({
        'status': 'ok',
        'database': 'connected',
        'version': '0.1.0',
        'environment': 'development',
      }, latencyMs: 14);

      expect(status.backendOk, isTrue);
      expect(status.databaseConnected, isTrue);
      expect(status.isFullyHealthy, isTrue);
      expect(status.version, '0.1.0');
      expect(status.environment, 'development');
      expect(status.latencyMs, 14);
    });

    test('parses partially healthy state (backend ok, db disconnected)', () {
      final status = HealthStatus.fromJson({
        'status': 'ok',
        'database': 'disconnected',
        'version': '0.1.0',
        'environment': 'development',
      });

      expect(status.backendOk, isTrue);
      expect(status.databaseConnected, isFalse);
      expect(status.isFullyHealthy, isFalse);
    });

    test('parses degraded/error state and handles missing JSON keys gracefully', () {
      final status = HealthStatus.fromJson(const {});

      expect(status.status, 'unknown');
      expect(status.database, 'unknown');
      expect(status.backendOk, isFalse);
      expect(status.databaseConnected, isFalse);
      expect(status.isFullyHealthy, isFalse);
    });
  });

  group('SearchRequest Model Tests', () {
    test('serializes default search request matching FastAPI schema', () {
      const request = SearchRequest(
        query: "What is Banker's algorithm?",
        userId: '00000000-0000-0000-0000-000000000001',
      );

      final json = request.toJson();
      expect(json['query'], "What is Banker's algorithm?");
      expect(json['user_id'], '00000000-0000-0000-0000-000000000001');
      expect(json['top_k'], 5);
      expect(json['min_similarity'], 0.2);
    });

    test('serializes custom parameters properly', () {
      const request = SearchRequest(
        query: 'deadlock prevention',
        userId: '18916e0d-b064-4724-b953-8b387239dd43',
        topK: 10,
        minSimilarity: 0.35,
      );

      final json = request.toJson();
      expect(json['top_k'], 10);
      expect(json['min_similarity'], 0.35);
    });
  });

  group('SearchResponse and ChunkSearchResult Model Tests', () {
    test('parses standard chunk search result response with metadata', () {
      final response = SearchResponse.fromJson({
        'query': "What is Banker's algorithm?",
        'total_results': 1,
        'results': [
          {
            'chunk_id': 'chunk-101',
            'memory_id': 'mem-202',
            'original_filename': 'OS_Unit_3_Deadlocks.pdf',
            'content':
                "Banker's Algorithm is a deadlock avoidance algorithm developed by Edsger Dijkstra.",
            'page_number': 5,
            'chunk_index': 2,
            'similarity_score': 0.4414,
            'chunk_metadata': {'topic': 'deadlock avoidance'},
          }
        ],
      });

      expect(response.totalResults, 1);
      expect(response.query, "What is Banker's algorithm?");
      final chunk = response.results.single;
      expect(chunk.chunkId, 'chunk-101');
      expect(chunk.originalFilename, 'OS_Unit_3_Deadlocks.pdf');
      expect(chunk.pageNumber, 5);
      expect(chunk.chunkIndex, 2);
      expect(chunk.similarityScore, 0.4414);
      expect(chunk.chunkMetadata['topic'], 'deadlock avoidance');
    });

    test('parses chunk without page number (text documents) and integer scores', () {
      final response = SearchResponse.fromJson({
        'query': 'notes',
        'results': [
          {
            'chunk_id': 'chunk-text-1',
            'memory_id': 'mem-text-1',
            'original_filename': 'notes.txt',
            'content': 'Raw text notes from meeting.',
            'page_number': null,
            'chunk_index': 0,
            'similarity_score': 1,
          }
        ],
      });

      expect(response.totalResults, 1);
      final chunk = response.results.single;
      expect(chunk.pageNumber, isNull);
      expect(chunk.similarityScore, 1.0);
      expect(chunk.chunkMetadata, isEmpty);
    });

    test('handles empty search results response gracefully', () {
      final response = SearchResponse.fromJson({
        'query': 'nonexistent query',
        'total_results': 0,
        'results': [],
      });

      expect(response.totalResults, 0);
      expect(response.results, isEmpty);
    });
  });

  group('MemoryItem & MemoryListResponse Model Tests', () {
    test('parses MemoryItem from backend JSON', () {
      final item = MemoryItem.fromJson({
        'id': '550e8400-e29b-41d4-a716-446655440000',
        'user_id': '00000000-0000-0000-0000-000000000001',
        'original_filename': 'Machine_Learning_Notes.pdf',
        'file_type': 'PDF',
        'file_path': './uploads/ml_notes.pdf',
        'file_size_bytes': 2048576,
        'status': 'processed',
        'created_at': '2026-11-07T10:00:00Z',
        'updated_at': '2026-11-07T10:00:00Z',
        'meta_info': {'page_count': 12},
      });

      expect(item.id, '550e8400-e29b-41d4-a716-446655440000');
      expect(item.originalFilename, 'Machine_Learning_Notes.pdf');
      expect(item.isPdf, isTrue);
      expect(item.isImage, isFalse);
      expect(item.isProcessed, isTrue);
      expect(item.formattedFileSize, '2.0 MB');
    });

    test('parses MemoryListResponse with multiple items', () {
      final list = MemoryListResponse.fromJson({
        'total': 2,
        'items': [
          {
            'id': 'id-1',
            'user_id': 'u-1',
            'original_filename': 'note.txt',
            'file_type': 'TEXT',
            'file_path': '/path/note.txt',
            'file_size_bytes': 1500,
            'status': 'processed',
          },
          {
            'id': 'id-2',
            'user_id': 'u-1',
            'original_filename': 'photo.png',
            'file_type': 'IMAGE',
            'file_path': '/path/photo.png',
            'file_size_bytes': 512000,
            'status': 'uploaded',
          },
        ],
      });

      expect(list.total, 2);
      expect(list.items.length, 2);
      expect(list.items.first.formattedFileSize, '1.5 KB');
      expect(list.items.last.isImage, isTrue);
    });
  });
}
