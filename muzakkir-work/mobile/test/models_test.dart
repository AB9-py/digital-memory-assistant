import 'package:digital_memory_assistant/models/health_status.dart';
import 'package:digital_memory_assistant/models/search_models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('parses health status response', () {
    final status = HealthStatus.fromJson({
      'status': 'ok',
      'database': 'connected',
      'version': '0.1.0',
      'environment': 'development',
    });

    expect(status.backendOk, isTrue);
    expect(status.databaseConnected, isTrue);
    expect(status.version, '0.1.0');
  });

  test('serializes search request with backend field names', () {
    const request = SearchRequest(
      query: 'What is deadlock prevention?',
      userId: '00000000-0000-0000-0000-000000000001',
      topK: 5,
      minSimilarity: 0.2,
    );

    expect(request.toJson(), {
      'query': 'What is deadlock prevention?',
      'user_id': '00000000-0000-0000-0000-000000000001',
      'top_k': 5,
      'min_similarity': 0.2,
    });
  });

  test('parses chunk search result response', () {
    final response = SearchResponse.fromJson({
      'query': 'deadlock',
      'total_results': 1,
      'results': [
        {
          'chunk_id': 'chunk-1',
          'memory_id': 'memory-1',
          'original_filename': 'OS_Unit_3.pdf',
          'content': 'Deadlock prevention eliminates one Coffman condition.',
          'page_number': 3,
          'chunk_index': 0,
          'similarity_score': 0.94,
          'chunk_metadata': {'section': 'Deadlocks'},
        }
      ],
    });

    expect(response.totalResults, 1);
    expect(response.results.single.originalFilename, 'OS_Unit_3.pdf');
    expect(response.results.single.pageNumber, 3);
    expect(response.results.single.similarityScore, 0.94);
  });
}
