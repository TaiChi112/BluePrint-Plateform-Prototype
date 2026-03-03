"""
Database Abstraction Layer for Spec Management
Supports multiple backends: FileSystem, PostgreSQL, MongoDB (future)
Current implementation: FileSystem (JSON files), PostgreSQL
"""

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


def _generate_spec_filename() -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    return f"spec_{timestamp}.json"


def _apply_spec_metadata(spec_data: Dict, filename: Optional[str] = None) -> Dict:
    final_filename = filename or spec_data.get("_filename") or _generate_spec_filename()
    saved_at = spec_data.get("_saved_at") or datetime.now().isoformat()
    return {
        **spec_data,
        "_saved_at": saved_at,
        "_filename": final_filename,
    }


class SpecRepository(ABC):
    """
    Abstract base class for Spec storage.
    Implement this class to support different backends (PostgreSQL, MongoDB, etc.)
    """

    @abstractmethod
    def save_spec(self, spec_data: Dict, filename: Optional[str] = None) -> str:
        """
        Save spec data and return filename/ID.

        Args:
            spec_data: Dictionary containing spec structure

        Returns:
            filename or ID of saved spec
        """
        pass

    @abstractmethod
    def load_spec(self, filename: str) -> Optional[Dict]:
        """
        Load spec by filename.

        Args:
            filename: Filename or ID to load

        Returns:
            Dictionary with spec data, or None if not found
        """
        pass

    @abstractmethod
    def list_all_specs(self) -> List[Dict]:
        """
        List all saved specs with metadata.

        Returns:
            List of dicts with keys: 'filename', 'project_name', 'created_at', 'status'
        """
        pass

    @abstractmethod
    def delete_spec(self, filename: str) -> bool:
        """
        Delete a spec by filename.

        Args:
            filename: Filename to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def get_spec_path(self, filename: str) -> Path:
        """
        Get the file path of a spec.

        Args:
            filename: Filename

        Returns:
            Path object
        """
        pass


class FileSystemRepository(SpecRepository):
    """
    JSON file-based repository implementation.
    Stores specs as JSON files in docs/json/ directory.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize FileSystemRepository.

        Args:
            base_dir: Base directory for spec storage. Defaults to docs/json/
        """
        if base_dir is None:
            # Get the parent directory of this script (project root)
            self.base_dir = Path(__file__).parent / "docs" / "json"
        else:
            self.base_dir = Path(base_dir)

        # Create directory if it doesn't exist
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_spec(self, spec_data: Dict, filename: Optional[str] = None) -> str:
        """
        Save spec to JSON file with auto-generated timestamp filename.
        Format: spec_YYYY-MM-DD-HH-MM.json

        Args:
            spec_data: Dictionary with spec data

        Returns:
            Filename of saved spec
        """
        spec_with_metadata = _apply_spec_metadata(spec_data, filename)
        filepath = self.base_dir / spec_with_metadata["_filename"]

        # Save to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(spec_with_metadata, f, indent=2, ensure_ascii=False)

        return spec_with_metadata["_filename"]

    def load_spec(self, filename: str) -> Optional[Dict]:
        """
        Load spec from JSON file.

        Args:
            filename: Filename to load (e.g., 'spec_2026-02-25-14-30.json')

        Returns:
            Dictionary with spec data, or None if file not found
        """
        filepath = self.base_dir / filename

        if not filepath.exists():
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def list_all_specs(self) -> List[Dict]:
        """
        List all saved specs with metadata, sorted by creation time (newest first).

        Returns:
            List of dicts with keys: 'filename', 'project_name', 'created_at', 'status'
        """
        specs = []

        # Get all .json files
        json_files = sorted(self.base_dir.glob("*.json"), reverse=True)

        for filepath in json_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Extract saved metadata
                saved_at = data.get("_saved_at", "")
                # Convert ISO format to readable format
                if saved_at:
                    try:
                        dt = datetime.fromisoformat(saved_at)
                        created_at = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        created_at = saved_at
                else:
                    created_at = "Unknown"

                specs.append(
                    {
                        "filename": filepath.name,
                        "project_name": data.get("project_name", "Untitled"),
                        "created_at": created_at,
                        "status": data.get("status", "Unknown"),
                    }
                )
            except (json.JSONDecodeError, IOError):
                # Skip files that can't be read
                continue

        return specs

    def delete_spec(self, filename: str) -> bool:
        """
        Delete a spec file.

        Args:
            filename: Filename to delete

        Returns:
            True if deleted, False if file not found
        """
        filepath = self.base_dir / filename

        if not filepath.exists():
            return False

        try:
            filepath.unlink()
            return True
        except OSError:
            return False

    def get_spec_path(self, filename: str) -> Path:
        """
        Get the file path of a spec.

        Args:
            filename: Filename

        Returns:
            Path object
        """
        return self.base_dir / filename


class PostgreSQLRepository(SpecRepository):
    """
    PostgreSQL database backend using Prisma schema (project_specs table).
    Requires psycopg2 and a running PostgreSQL database.

    Environment variables:
        DB_HOST: PostgreSQL host (default: localhost)
        DB_PORT: PostgreSQL port (default: 5432)
        DB_USER: PostgreSQL user (default: specuser)
        DB_PASSWORD: PostgreSQL password (default: specpassword123)
        DB_NAME: Database name (default: auto_spec_db)
    """

    def __init__(self):
        """Initialize PostgreSQL connection."""
        if not HAS_PSYCOPG2:
            raise ImportError(
                "psycopg2 is required for PostgreSQL backend. "
                "Install it with: pip install psycopg2-binary"
            )

        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "user": os.getenv("DB_USER", "specuser"),
            "password": os.getenv("DB_PASSWORD", "specpassword123"),
            "database": os.getenv("DB_NAME", "auto_spec_db"),
        }

        # Test connection
        try:
            conn = psycopg2.connect(**self.db_config)
            conn.close()
        except psycopg2.Error as e:
            raise RuntimeError(
                f"Failed to connect to PostgreSQL: {e}\n"
                f"Make sure PostgreSQL is running and credentials are correct."
            )

    def _get_connection(self):
        """Get a database connection."""
        return psycopg2.connect(**self.db_config)

    def save_spec(self, spec_data: Dict, user_id: Optional[str] = None, filename: Optional[str] = None) -> str:
        """
        Save spec to PostgreSQL project_specs table (Prisma schema).

        Args:
            spec_data: Dictionary with spec data
            user_id: User ID (optional, can be "system" if not provided)
            filename: Filename/identifier

        Returns:
            Filename of saved spec
        """
        spec_with_metadata = _apply_spec_metadata(spec_data, filename)
        final_filename = spec_with_metadata["_filename"]
        user_id = user_id or "system"

        try:
            conn = self._get_connection()
            cur = conn.cursor()

            # Insert into project_specs table (Prisma schema)
            # Arrays are stored as PostgreSQL text arrays
            cur.execute(
                """
                INSERT INTO project_specs (
                    id, "userId", "projectName", "problemStatement",
                    "solutionOverview", "functionalRequirements",
                    "nonFunctionalRequirements", "techStackRecommendation",
                    status, "isPublished", "savedAt", "createdAt", "updatedAt"
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    final_filename,  # Use filename as ID temporarily
                    user_id,
                    spec_data.get("project_name", "Untitled"),
                    spec_data.get("problem_statement", ""),
                    spec_data.get("solution_overview", ""),
                    spec_data.get("functional_requirements", []),  # PostgreSQL array
                    spec_data.get("non_functional_requirements", []),  # PostgreSQL array
                    spec_data.get("tech_stack_recommendation", []),  # PostgreSQL array
                    spec_data.get("status", "Draft"),
                    spec_data.get("isPublished", True),
                    datetime.now().isoformat(),  # savedAt
                    datetime.now().isoformat(),  # createdAt
                    datetime.now().isoformat(),  # updatedAt
                ),
            )

            conn.commit()
            cur.close()
            conn.close()

            return final_filename

        except psycopg2.Error as e:
            raise RuntimeError(f"Database error while saving spec: {e}")

    def load_spec(self, filename: str) -> Optional[Dict]:
        """
        Load spec from PostgreSQL project_specs table.

        Args:
            filename: Filename/ID to load

        Returns:
            Dictionary with spec data, or None if not found
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute(
                """
                SELECT
                    id, "userId", "projectName", "problemStatement",
                    "solutionOverview", "functionalRequirements",
                    "nonFunctionalRequirements", "techStackRecommendation",
                    status, "isPublished", "savedAt", "createdAt", "updatedAt"
                FROM project_specs
                WHERE id = %s
                """,
                (filename,),
            )
            spec_row = cur.fetchone()

            cur.close()
            conn.close()

            if not spec_row:
                return None

            # Return spec data in expected format
            return {
                "id": spec_row["id"],
                "userId": spec_row["userId"],
                "project_name": spec_row["projectName"],
                "problem_statement": spec_row["problemStatement"],
                "solution_overview": spec_row["solutionOverview"],
                "functional_requirements": spec_row["functionalRequirements"] or [],
                "non_functional_requirements": spec_row["nonFunctionalRequirements"] or [],
                "tech_stack_recommendation": spec_row["techStackRecommendation"] or [],
                "status": spec_row["status"],
                "isPublished": spec_row["isPublished"],
                "savedAt": spec_row["savedAt"],
                "createdAt": spec_row["createdAt"],
                "updatedAt": spec_row["updatedAt"],
                "_filename": spec_row["id"],
            }

        except psycopg2.Error as e:
            print(f"Database error while loading spec: {e}")
            return None

    def list_all_specs(self, user_id: Optional[str] = None) -> List[Dict]:
        """
        List all saved specs with metadata, filtered by user if provided.

        Args:
            user_id: Optional user ID to filter specs

        Returns:
            List of dicts with spec metadata
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            if user_id:
                cur.execute(
                    """
                    SELECT id, "projectName", status, "createdAt"
                    FROM project_specs
                    WHERE "userId" = %s
                    ORDER BY "createdAt" DESC
                    """,
                    (user_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT id, "projectName", status, "createdAt"
                    FROM project_specs
                    ORDER BY "createdAt" DESC
                    """
                )

            specs = []
            for row in cur.fetchall():
                created_at = row["createdAt"]
                if isinstance(created_at, str):
                    created_at = created_at.split("T")[0]  # Just the date part
                else:
                    created_at = created_at.strftime("%Y-%m-%d %H:%M")

                specs.append(
                    {
                        "filename": row["id"],
                        "project_name": row["projectName"],
                        "created_at": created_at,
                        "status": row["status"],
                    }
                )

            cur.close()
            conn.close()
            return specs

        except psycopg2.Error as e:
            print(f"Database error while listing specs: {e}")
            return []

    def delete_spec(self, filename: str) -> bool:
        """
        Delete a spec from project_specs table.

        Args:
            filename: ID/filename to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()

            cur.execute("DELETE FROM project_specs WHERE id = %s", (filename,))
            deleted_count = cur.rowcount

            conn.commit()
            cur.close()
            conn.close()

            return deleted_count > 0

        except psycopg2.Error as e:
            print(f"Database error while deleting spec: {e}")
            return False

    def get_spec_path(self, filename: str) -> Path:
        """
        Get the identifier of a spec.

        Args:
            filename: ID/filename

        Returns:
            Path object
        """
        return Path(filename)


class DualRepository(SpecRepository):
    """
    Composite repository that saves to both FileSystem and PostgreSQL.
    PostgreSQL is optional; if unavailable, it falls back to FileSystem only.
    """

    def __init__(self):
        self.file_repo = FileSystemRepository()
        self.postgres_repo = None
        self.postgres_available = False
        self.postgres_error = None
        self.last_save_result = {}

        try:
            self.postgres_repo = PostgreSQLRepository()
            self.postgres_available = True
        except Exception as e:
            self.postgres_error = str(e)

    def save_spec(self, spec_data: Dict, user_id: Optional[str] = None, filename: Optional[str] = None) -> str:
        """
        Save spec to both FileSystem and PostgreSQL.

        Args:
            spec_data: Spec data to save
            user_id: User ID who created this spec
            filename: Optional filename override

        Returns:
            Filename/ID of saved spec
        """
        spec_with_metadata = _apply_spec_metadata(spec_data, filename)
        final_filename = spec_with_metadata["_filename"]

        file_saved = False
        postgres_saved = False
        postgres_error = None
        file_error = None

        # Save to FileSystem
        try:
            self.file_repo.save_spec(spec_with_metadata, final_filename)
            file_saved = True
        except Exception as e:
            file_error = str(e)

        # Save to PostgreSQL
        if self.postgres_available and self.postgres_repo:
            try:
                self.postgres_repo.save_spec(spec_with_metadata, user_id, final_filename)
                postgres_saved = True
            except Exception as e:
                postgres_error = str(e)
        else:
            postgres_error = self.postgres_error

        self.last_save_result = {
            "filename": final_filename,
            "file_saved": file_saved,
            "file_error": file_error,
            "postgres_saved": postgres_saved,
            "postgres_error": postgres_error,
        }

        if not file_saved and not postgres_saved:
            raise RuntimeError(
                f"Failed to save spec. File error: {file_error}, Postgres error: {postgres_error}"
            )

        return final_filename

    def load_spec(self, filename: str) -> Optional[Dict]:
        if self.postgres_available and self.postgres_repo:
            data = self.postgres_repo.load_spec(filename)
            if data:
                return data
        return self.file_repo.load_spec(filename)

    def list_all_specs(self, user_id: Optional[str] = None) -> List[Dict]:
        """
        List all specs, optionally filtered by user.

        Args:
            user_id: Optional user ID to filter specs

        Returns:
            List of spec metadata
        """
        file_specs = self.file_repo.list_all_specs()
        db_specs = []

        if self.postgres_available and self.postgres_repo:
            db_specs = self.postgres_repo.list_all_specs(user_id)

        merged = {}
        for spec in file_specs:
            merged[spec["filename"]] = spec
        for spec in db_specs:
            if spec["filename"] in merged:
                merged[spec["filename"]] = {**merged[spec["filename"]], **spec}
            else:
                merged[spec["filename"]] = spec

        def _sort_key(item):
            created_at = item.get("created_at", "")
            try:
                return datetime.strptime(created_at, "%Y-%m-%d %H:%M")
            except Exception:
                return datetime.min

        return sorted(merged.values(), key=_sort_key, reverse=True)

    def delete_spec(self, filename: str) -> bool:
        file_deleted = self.file_repo.delete_spec(filename)
        db_deleted = False

        if self.postgres_available and self.postgres_repo:
            db_deleted = self.postgres_repo.delete_spec(filename)

        return file_deleted or db_deleted

    def get_spec_path(self, filename: str) -> Path:
        return self.file_repo.get_spec_path(filename)


# Future implementations (TODO):
# class MongoDBRepository(SpecRepository):
#     """MongoDB database backend"""
#     pass
