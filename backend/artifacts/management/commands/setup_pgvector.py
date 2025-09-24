"""
Django management command to setup pgvector extension and verify vector operations.
"""

import numpy as np
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Setup pgvector extension and verify vector operations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-vectors',
            action='store_true',
            help='Test vector operations with sample data'
        )

    def handle(self, *args, **options):
        self.test_vectors = options['test_vectors']

        # Check if we're using PostgreSQL
        if 'postgresql' not in settings.DATABASES['default']['ENGINE']:
            raise CommandError(
                'This command requires PostgreSQL database. '
                'Current engine: ' + settings.DATABASES['default']['ENGINE']
            )

        self.stdout.write("Setting up pgvector extension...")

        try:
            self.install_pgvector()
            self.verify_pgvector()

            if self.test_vectors:
                self.test_vector_operations()

            self.stdout.write(
                self.style.SUCCESS("pgvector setup completed successfully!")
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"pgvector setup failed: {str(e)}")
            )
            raise

    def install_pgvector(self):
        """Install pgvector extension."""

        with connection.cursor() as cursor:
            # Install pgvector extension
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

            self.stdout.write(
                self.style.SUCCESS("✓ pgvector extension installed")
            )

    def verify_pgvector(self):
        """Verify pgvector installation."""

        with connection.cursor() as cursor:
            # Check if extension is installed
            cursor.execute("""
                SELECT extname, extversion
                FROM pg_extension
                WHERE extname = 'vector'
            """)

            result = cursor.fetchone()
            if result:
                extname, extversion = result
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ pgvector extension verified: {extname} v{extversion}"
                    )
                )
            else:
                raise CommandError("pgvector extension not found")

            # Test basic vector operation
            cursor.execute("SELECT vector_dims(ARRAY[1,2,3]::vector);")
            dims = cursor.fetchone()[0]

            if dims == 3:
                self.stdout.write(
                    self.style.SUCCESS("✓ Vector operations working correctly")
                )
            else:
                raise CommandError("Vector operations not working correctly")

    def test_vector_operations(self):
        """Test vector operations with sample data."""

        self.stdout.write("Testing vector operations...")

        with connection.cursor() as cursor:
            # Create test table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_vectors (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    embedding VECTOR(1536)
                );
            """)

            # Clear existing test data
            cursor.execute("DELETE FROM test_vectors;")

            # Generate sample 1536-dimensional vectors (matching OpenAI embeddings)
            sample_vectors = []
            vector_names = ["document_1", "document_2", "document_3"]

            for name in vector_names:
                # Generate random normalized vector
                vector = np.random.rand(1536)
                vector = vector / np.linalg.norm(vector)  # Normalize
                sample_vectors.append((name, vector.tolist()))

            # Insert test vectors
            for name, vector in sample_vectors:
                cursor.execute(
                    "INSERT INTO test_vectors (name, embedding) VALUES (%s, %s);",
                    [name, vector]
                )

            self.stdout.write("✓ Inserted test vectors")

            # Test similarity search using cosine distance
            query_vector = sample_vectors[0][1]  # Use first vector as query

            cursor.execute("""
                SELECT
                    name,
                    embedding <=> %s::vector as cosine_distance
                FROM test_vectors
                ORDER BY embedding <=> %s::vector
                LIMIT 3;
            """, [query_vector, query_vector])

            results = cursor.fetchall()

            self.stdout.write("Similarity search results (cosine distance):")
            for name, distance in results:
                self.stdout.write(f"  {name}: {distance:.4f}")

            # Verify first result has distance 0 (identical vectors)
            if len(results) > 0 and abs(results[0][1]) < 0.0001:
                self.stdout.write(
                    self.style.SUCCESS("✓ Cosine distance calculation correct")
                )
            else:
                raise CommandError("Cosine distance calculation incorrect")

            # Test L2 distance
            cursor.execute("""
                SELECT
                    name,
                    embedding <-> %s::vector as l2_distance
                FROM test_vectors
                ORDER BY embedding <-> %s::vector
                LIMIT 3;
            """, [query_vector, query_vector])

            l2_results = cursor.fetchall()

            self.stdout.write("L2 distance results:")
            for name, distance in l2_results:
                self.stdout.write(f"  {name}: {distance:.4f}")

            if len(l2_results) > 0 and abs(l2_results[0][1]) < 0.0001:
                self.stdout.write(
                    self.style.SUCCESS("✓ L2 distance calculation correct")
                )
            else:
                raise CommandError("L2 distance calculation incorrect")

            # Test inner product
            cursor.execute("""
                SELECT
                    name,
                    (embedding <#> %s::vector) * -1 as inner_product
                FROM test_vectors
                ORDER BY embedding <#> %s::vector DESC
                LIMIT 3;
            """, [query_vector, query_vector])

            ip_results = cursor.fetchall()

            self.stdout.write("Inner product results:")
            for name, product in ip_results:
                self.stdout.write(f"  {name}: {product:.4f}")

            # Test vector indexing (create index and test performance)
            self.stdout.write("Testing vector indexing...")

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS test_vectors_embedding_cosine_idx
                ON test_vectors USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 1);
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS test_vectors_embedding_l2_idx
                ON test_vectors USING ivfflat (embedding vector_l2_ops)
                WITH (lists = 1);
            """)

            self.stdout.write("✓ Vector indexes created")

            # Test index usage with EXPLAIN
            cursor.execute("""
                EXPLAIN (FORMAT JSON)
                SELECT name, embedding <=> %s::vector as distance
                FROM test_vectors
                ORDER BY embedding <=> %s::vector
                LIMIT 1;
            """, [query_vector, query_vector])

            explain_result = cursor.fetchone()[0]
            self.stdout.write("Query plan created (index should be used)")

            # Cleanup test table
            cursor.execute("DROP TABLE test_vectors;")

            self.stdout.write(
                self.style.SUCCESS("✓ Vector operations test completed successfully")
            )