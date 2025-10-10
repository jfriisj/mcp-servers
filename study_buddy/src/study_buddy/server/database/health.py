"""
Database health monitoring and diagnostics for Study Buddy MCP Server.

Provides comprehensive database performance monitoring, health checks,
and diagnostic capabilities using SQLite PRAGMA commands and system metrics.
"""

import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List

from ..database.connection import DatabaseConnection


class DatabaseHealthMetrics:
    """
    Database health and performance metrics container.

    Encapsulates all health-related data for easy serialization
    and reporting following Single Responsibility Principle.
    """

    def __init__(self):
        self.timestamp = datetime.now()
        self.database_info: Dict[str, Any] = {}
        self.performance_metrics: Dict[str, Any] = {}
        self.index_health: Dict[str, Any] = {}
        self.table_statistics: Dict[str, Any] = {}
        self.connection_info: Dict[str, Any] = {}
        self.warnings: List[str] = []
        self.recommendations: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "database_info": self.database_info,
            "performance_metrics": self.performance_metrics,
            "index_health": self.index_health,
            "table_statistics": self.table_statistics,
            "connection_info": self.connection_info,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "overall_health": self.calculate_overall_health()
        }

    def calculate_overall_health(self) -> str:
        """
        Calculate overall health status based on metrics.

        Returns:
            Health status: "healthy", "warning", "critical"
        """
        warning_count = len(self.warnings)

        if warning_count == 0:
            return "healthy"
        elif warning_count <= 2:
            return "warning"
        else:
            return "critical"


class DatabaseHealthMonitor:
    """
    Comprehensive database health monitoring and diagnostics system.

    This class follows Clean Architecture Layer 4 principles by providing
    infrastructure concerns for database monitoring and performance analysis:

    - Real-time health metrics collection using SQLite PRAGMA commands
    - Performance monitoring with query execution time tracking
    - Database size and storage analytics
    - Index health validation and optimization suggestions
    - Connection pool monitoring and resource usage analysis

    SOLID Principles Applied:
    - SRP: Only manages database health monitoring and diagnostics
    - OCP: Extensible for new health metrics without modification
    - DIP: Depends on DatabaseConnection abstraction
    - ISP: Focused interface for health monitoring only
    """

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize health monitor.

        Args:
            db_connection: Database connection manager
        """
        self.db = db_connection
        self.logger = logging.getLogger(__name__)

    def collect_comprehensive_health_metrics(self) -> DatabaseHealthMetrics:
        """
        Collect comprehensive health metrics for database diagnostics.

        Returns:
            DatabaseHealthMetrics with complete health information
        """
        metrics = DatabaseHealthMetrics()

        try:
            # Collect all metric categories
            metrics.database_info = self.get_database_info()
            metrics.performance_metrics = self.get_performance_metrics()
            metrics.index_health = self.analyze_index_health()
            metrics.table_statistics = self.get_table_statistics()
            metrics.connection_info = self.get_connection_info()

            # Generate warnings and recommendations
            self._generate_warnings_and_recommendations(metrics)

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to collect health metrics: {str(e)}")
            raise

    def get_database_info(self) -> Dict[str, Any]:
        """
        Get basic database information using PRAGMA commands.

        Returns:
            Dictionary with database configuration and status
        """
        cursor = self.db.cursor()
        info = {}

        try:
            # Basic database information
            cursor.execute("PRAGMA user_version")
            info["user_version"] = cursor.fetchone()[0]

            cursor.execute("PRAGMA schema_version")
            info["schema_version"] = cursor.fetchone()[0]

            cursor.execute("PRAGMA application_id")
            info["application_id"] = cursor.fetchone()[0]

            # SQLite version
            cursor.execute("SELECT sqlite_version()")
            info["sqlite_version"] = cursor.fetchone()[0]

            # Database configuration
            cursor.execute("PRAGMA journal_mode")
            info["journal_mode"] = cursor.fetchone()[0]

            cursor.execute("PRAGMA synchronous")
            info["synchronous_mode"] = cursor.fetchone()[0]

            cursor.execute("PRAGMA foreign_keys")
            info["foreign_keys_enabled"] = bool(cursor.fetchone()[0])

            cursor.execute("PRAGMA temp_store")
            info["temp_store"] = cursor.fetchone()[0]

            cursor.execute("PRAGMA cache_size")
            info["cache_size_kb"] = cursor.fetchone()[0] * -1  # Convert pages to KB

            # File information
            if hasattr(self.db, 'database_path') and os.path.exists(self.db.database_path):
                stat = os.stat(self.db.database_path)
                info["file_size_bytes"] = stat.st_size
                info["file_size_mb"] = round(stat.st_size / (1024 * 1024), 2)
                info["last_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()

            return info

        except Exception as e:
            self.logger.error(f"Failed to get database info: {str(e)}")
            return {"error": str(e)}

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Collect database performance metrics.

        Returns:
            Dictionary with performance statistics
        """
        cursor = self.db.cursor()
        metrics = {}

        try:
            # Query performance stats
            start_time = time.time()
            cursor.execute("SELECT COUNT(*) FROM documents")
            query_time = (time.time() - start_time) * 1000  # Convert to ms
            metrics["simple_query_time_ms"] = round(query_time, 2)

            # FTS5 search performance test
            start_time = time.time()
            cursor.execute("SELECT COUNT(*) FROM documents_fts WHERE documents_fts MATCH 'test OR sample'")
            fts_time = (time.time() - start_time) * 1000
            metrics["fts_query_time_ms"] = round(fts_time, 2)

            # Compile options
            cursor.execute("PRAGMA compile_options")
            compile_options = [row[0] for row in cursor.fetchall()]
            metrics["compile_options"] = compile_options

            # Memory usage
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]

            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]

            metrics["total_pages"] = page_count
            metrics["page_size_bytes"] = page_size
            metrics["database_size_mb"] = round((page_count * page_size) / (1024 * 1024), 2)

            # Free pages
            cursor.execute("PRAGMA freelist_count")
            free_pages = cursor.fetchone()[0]
            metrics["free_pages"] = free_pages
            metrics["fragmentation_percent"] = round((free_pages / max(page_count, 1)) * 100, 2) if page_count > 0 else 0

            # WAL mode info (if applicable)
            try:
                cursor.execute("PRAGMA wal_autocheckpoint")
                metrics["wal_autocheckpoint"] = cursor.fetchone()[0]

                cursor.execute("PRAGMA wal_checkpoint")
                wal_result = cursor.fetchone()
                if wal_result:
                    metrics["wal_checkpoint_result"] = {
                        "busy": wal_result[0],
                        "log_pages": wal_result[1],
                        "checkpointed_pages": wal_result[2]
                    }
            except:
                # WAL mode not enabled
                metrics["wal_mode_enabled"] = False

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {str(e)}")
            return {"error": str(e)}

    def analyze_index_health(self) -> Dict[str, Any]:
        """
        Analyze database index health and usage statistics.

        Returns:
            Dictionary with index analysis results
        """
        cursor = self.db.cursor()
        analysis = {"indexes": [], "recommendations": []}

        try:
            # Get all indexes
            cursor.execute("""
                SELECT name, tbl_name, sql
                FROM sqlite_master
                WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)

            indexes = cursor.fetchall()

            for index_name, table_name, index_sql in indexes:
                index_info = {
                    "name": index_name,
                    "table": table_name,
                    "sql": index_sql
                }

                # Get index statistics
                try:
                    cursor.execute(f"PRAGMA index_info({index_name})")
                    columns = cursor.fetchall()
                    index_info["columns"] = [col[2] for col in columns]

                    cursor.execute(f"PRAGMA index_xinfo({index_name})")
                    extended_info = cursor.fetchall()
                    index_info["column_count"] = len(extended_info)

                except Exception as e:
                    index_info["error"] = str(e)

                analysis["indexes"].append(index_info)

            # Check for missing indexes on foreign keys
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            """)

            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                try:
                    cursor.execute(f"PRAGMA foreign_key_list({table})")
                    foreign_keys = cursor.fetchall()

                    for fk in foreign_keys:
                        fk_column = fk[3]  # from column

                        # Check if there's an index on this foreign key
                        cursor.execute("""
                            SELECT COUNT(*) FROM sqlite_master
                            WHERE type = 'index'
                            AND tbl_name = ?
                            AND sql LIKE '%' || ? || '%'
                        """, (table, fk_column))

                        has_index = cursor.fetchone()[0] > 0

                        if not has_index:
                            analysis["recommendations"].append(
                                f"Consider adding index on {table}.{fk_column} (foreign key)"
                            )

                except Exception as e:
                    self.logger.warning(f"Could not analyze foreign keys for table {table}: {str(e)}")

            # Analyze FTS5 virtual table health
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type = 'table' AND sql LIKE '%fts5%'
            """)

            fts_tables = [row[0] for row in cursor.fetchall()]
            analysis["fts_tables"] = []

            for fts_table in fts_tables:
                try:
                    # Get FTS5 statistics
                    cursor.execute(f"INSERT INTO {fts_table}({fts_table}) VALUES('integrity-check')")

                    cursor.execute(f"INSERT INTO {fts_table}({fts_table}) VALUES('optimize')")

                    analysis["fts_tables"].append({
                        "name": fts_table,
                        "status": "healthy",
                        "optimized": True
                    })

                except Exception as e:
                    analysis["fts_tables"].append({
                        "name": fts_table,
                        "status": "error",
                        "error": str(e)
                    })

            return analysis

        except Exception as e:
            self.logger.error(f"Failed to analyze index health: {str(e)}")
            return {"error": str(e)}

    def get_table_statistics(self) -> Dict[str, Any]:
        """
        Get detailed table statistics and row counts.

        Returns:
            Dictionary with table statistics
        """
        cursor = self.db.cursor()
        statistics = {"tables": {}}

        try:
            # Get all user tables
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type = 'table'
                AND name NOT LIKE 'sqlite_%'
                AND name NOT LIKE '%_fts%'
                ORDER BY name
            """)

            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                try:
                    # Row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]

                    # Table info
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()

                    statistics["tables"][table] = {
                        "row_count": row_count,
                        "column_count": len(columns),
                        "columns": [
                            {
                                "name": col[1],
                                "type": col[2],
                                "not_null": bool(col[3]),
                                "default_value": col[4],
                                "primary_key": bool(col[5])
                            }
                            for col in columns
                        ]
                    }

                    # Additional statistics for main tables
                    if table in ["documents", "chunks", "summaries"]:
                        if table == "documents":
                            cursor.execute("SELECT file_type, COUNT(*) FROM documents GROUP BY file_type")
                            file_types = dict(cursor.fetchall())
                            statistics["tables"][table]["file_type_distribution"] = file_types

                            cursor.execute("SELECT COUNT(*) FROM documents WHERE indexed = 1")
                            indexed_count = cursor.fetchone()[0]
                            statistics["tables"][table]["indexed_documents"] = indexed_count

                        elif table == "chunks":
                            cursor.execute("SELECT chunk_type, COUNT(*) FROM chunks GROUP BY chunk_type")
                            chunk_types = dict(cursor.fetchall())
                            statistics["tables"][table]["chunk_type_distribution"] = chunk_types

                        elif table == "summaries":
                            cursor.execute("SELECT summary_type, COUNT(*) FROM summaries GROUP BY summary_type")
                            summary_types = dict(cursor.fetchall())
                            statistics["tables"][table]["summary_type_distribution"] = summary_types

                except Exception as e:
                    statistics["tables"][table] = {"error": str(e)}

            # Overall statistics
            total_rows = sum(
                table_stats.get("row_count", 0)
                for table_stats in statistics["tables"].values()
                if isinstance(table_stats, dict) and "row_count" in table_stats
            )

            statistics["summary"] = {
                "total_tables": len(tables),
                "total_rows": total_rows,
                "largest_table": max(
                    statistics["tables"].items(),
                    key=lambda x: x[1].get("row_count", 0) if isinstance(x[1], dict) else 0,
                    default=(None, {})
                )[0] if statistics["tables"] else None
            }

            return statistics

        except Exception as e:
            self.logger.error(f"Failed to get table statistics: {str(e)}")
            return {"error": str(e)}

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get database connection and threading information.

        Returns:
            Dictionary with connection statistics
        """
        info = {}

        try:
            # Connection info
            info["database_path"] = getattr(self.db, 'database_path', 'unknown')
            info["connection_active"] = True  # If we can call this, connection is active

            cursor = self.db.cursor()

            # Thread safety info
            cursor.execute("PRAGMA threads")
            info["thread_count"] = cursor.fetchone()[0]

            # Locking mode
            cursor.execute("PRAGMA locking_mode")
            info["locking_mode"] = cursor.fetchone()[0]

            # Read uncommitted
            cursor.execute("PRAGMA read_uncommitted")
            info["read_uncommitted"] = bool(cursor.fetchone()[0])

            # Busy timeout
            cursor.execute("PRAGMA busy_timeout")
            info["busy_timeout_ms"] = cursor.fetchone()[0]

            return info

        except Exception as e:
            self.logger.error(f"Failed to get connection info: {str(e)}")
            return {"error": str(e)}

    def _generate_warnings_and_recommendations(self, metrics: DatabaseHealthMetrics) -> None:
        """
        Generate health warnings and optimization recommendations.

        Args:
            metrics: DatabaseHealthMetrics to analyze and update
        """
        # Check database size warnings
        if "file_size_mb" in metrics.database_info:
            size_mb = metrics.database_info["file_size_mb"]
            if size_mb > 1000:  # Over 1GB
                metrics.warnings.append(f"Large database size: {size_mb}MB")
                metrics.recommendations.append("Consider archiving old data or implementing data retention policies")

        # Check fragmentation
        if "fragmentation_percent" in metrics.performance_metrics:
            fragmentation = metrics.performance_metrics["fragmentation_percent"]
            if fragmentation > 10:
                metrics.warnings.append(f"High fragmentation: {fragmentation}%")
                metrics.recommendations.append("Consider running VACUUM to defragment database")

        # Check query performance
        if "simple_query_time_ms" in metrics.performance_metrics:
            query_time = metrics.performance_metrics["simple_query_time_ms"]
            if query_time > 100:  # Over 100ms for simple query
                metrics.warnings.append(f"Slow query performance: {query_time}ms for simple query")
                metrics.recommendations.append("Consider optimizing indexes or upgrading hardware")

        # Check FTS5 performance
        if "fts_query_time_ms" in metrics.performance_metrics:
            fts_time = metrics.performance_metrics["fts_query_time_ms"]
            if fts_time > 500:  # Over 500ms for FTS query
                metrics.warnings.append(f"Slow FTS5 search: {fts_time}ms")
                metrics.recommendations.append("Consider rebuilding FTS5 indexes or optimizing search queries")

        # Check foreign keys
        if "foreign_keys_enabled" in metrics.database_info:
            if not metrics.database_info["foreign_keys_enabled"]:
                metrics.warnings.append("Foreign keys are disabled")
                metrics.recommendations.append("Enable foreign keys with PRAGMA foreign_keys = ON")

        # Check WAL mode
        if "journal_mode" in metrics.database_info:
            if metrics.database_info["journal_mode"] != "wal":
                metrics.recommendations.append("Consider enabling WAL mode for better concurrent access")

        # Check index recommendations
        if "recommendations" in metrics.index_health:
            metrics.recommendations.extend(metrics.index_health["recommendations"])

    def run_maintenance_operations(self) -> Dict[str, Any]:
        """
        Run database maintenance operations.

        Returns:
            Dictionary with maintenance operation results
        """
        cursor = self.db.cursor()
        results = {}

        try:
            # Analyze tables to update statistics
            start_time = time.time()
            cursor.execute("ANALYZE")
            results["analyze_duration_ms"] = round((time.time() - start_time) * 1000, 2)

            # Optimize FTS5 indexes
            fts_results = []
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type = 'table' AND sql LIKE '%fts5%'
            """)

            fts_tables = [row[0] for row in cursor.fetchall()]

            for fts_table in fts_tables:
                try:
                    start_time = time.time()
                    cursor.execute(f"INSERT INTO {fts_table}({fts_table}) VALUES('optimize')")
                    optimize_time = round((time.time() - start_time) * 1000, 2)
                    fts_results.append({
                        "table": fts_table,
                        "optimize_duration_ms": optimize_time,
                        "status": "success"
                    })
                except Exception as e:
                    fts_results.append({
                        "table": fts_table,
                        "status": "error",
                        "error": str(e)
                    })

            results["fts_optimization"] = fts_results

            # Check if VACUUM would be beneficial
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]

            cursor.execute("PRAGMA freelist_count")
            free_pages = cursor.fetchone()[0]

            fragmentation = (free_pages / max(page_count, 1)) * 100 if page_count > 0 else 0

            results["fragmentation_check"] = {
                "total_pages": page_count,
                "free_pages": free_pages,
                "fragmentation_percent": round(fragmentation, 2),
                "vacuum_recommended": fragmentation > 10
            }

            self.db.commit()
            return results

        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Maintenance operations failed: {str(e)}")
            return {"error": str(e)}

    def validate_database_integrity(self) -> Dict[str, Any]:
        """
        Validate database integrity using SQLite integrity checks.

        Returns:
            Dictionary with integrity check results
        """
        cursor = self.db.cursor()
        results = {}

        try:
            # Full integrity check
            start_time = time.time()
            cursor.execute("PRAGMA integrity_check")
            integrity_results = cursor.fetchall()

            results["integrity_check"] = {
                "duration_ms": round((time.time() - start_time) * 1000, 2),
                "status": "ok" if integrity_results == [("ok",)] else "errors",
                "results": [row[0] for row in integrity_results]
            }

            # Quick check (faster alternative)
            start_time = time.time()
            cursor.execute("PRAGMA quick_check")
            quick_results = cursor.fetchall()

            results["quick_check"] = {
                "duration_ms": round((time.time() - start_time) * 1000, 2),
                "status": "ok" if quick_results == [("ok",)] else "errors",
                "results": [row[0] for row in quick_results]
            }

            # Foreign key check
            start_time = time.time()
            cursor.execute("PRAGMA foreign_key_check")
            fk_violations = cursor.fetchall()

            results["foreign_key_check"] = {
                "duration_ms": round((time.time() - start_time) * 1000, 2),
                "violations": len(fk_violations),
                "details": [
                    {
                        "table": row[0],
                        "rowid": row[1],
                        "parent": row[2],
                        "fkid": row[3]
                    }
                    for row in fk_violations
                ] if fk_violations else []
            }

            return results

        except Exception as e:
            self.logger.error(f"Integrity validation failed: {str(e)}")
            return {"error": str(e)}
