#!/usr/bin/env python3
"""
UATP Data Storage Consolidation Script
Analyze and consolidate JSONL and SQLite data to eliminate redundancy
"""
import json
import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


class DataStorageAnalyzer:
    def __init__(
        self, jsonl_path: str = "capsule_chain.jsonl", db_path: str = "uatp_dev.db"
    ):
        self.jsonl_path = Path(jsonl_path)
        self.db_path = Path(db_path)
        self.jsonl_capsules = []
        self.db_capsules = []

    def analyze_jsonl_file(self) -> Dict[str, Any]:
        """Analyze JSONL file structure and content"""
        print("📄 Analyzing JSONL file...")

        if not self.jsonl_path.exists():
            return {"exists": False, "error": "JSONL file not found"}

        try:
            capsule_ids = set()
            line_count = 0

            with open(self.jsonl_path, "r") as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            capsule = json.loads(line)
                            self.jsonl_capsules.append(capsule)

                            # Extract capsule ID
                            capsule_id = capsule.get("id") or capsule.get("capsule_id")
                            if capsule_id:
                                capsule_ids.add(capsule_id)

                            line_count += 1
                        except json.JSONDecodeError as e:
                            print(f"⚠️  Invalid JSON on line {line_num}: {e}")

            file_size = self.jsonl_path.stat().st_size

            return {
                "exists": True,
                "file_size": file_size,
                "line_count": line_count,
                "unique_capsules": len(capsule_ids),
                "capsule_ids": list(capsule_ids)[:10],  # First 10 for preview
                "average_size_per_capsule": file_size / line_count
                if line_count > 0
                else 0,
            }

        except Exception as e:
            return {"exists": True, "error": str(e)}

    def analyze_sqlite_db(self) -> Dict[str, Any]:
        """Analyze SQLite database structure and content"""
        print("🗄️  Analyzing SQLite database...")

        if not self.db_path.exists():
            return {"exists": False, "error": "SQLite database not found"}

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]

            table_info = {}
            total_records = 0

            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                total_records += count

                # Get table schema
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]

                table_info[table] = {"record_count": count, "columns": columns}

                # If this looks like a capsules table, get some sample data
                if "capsule" in table.lower() and count > 0:
                    cursor.execute(f"SELECT * FROM {table} LIMIT 5")
                    sample_records = cursor.fetchall()
                    table_info[table]["sample_data"] = len(sample_records)

                    # Try to extract capsule IDs
                    if "id" in columns:
                        cursor.execute(f"SELECT id FROM {table}")
                        capsule_ids = [row[0] for row in cursor.fetchall()]
                        table_info[table]["capsule_ids"] = capsule_ids[:10]

            file_size = self.db_path.stat().st_size

            conn.close()

            return {
                "exists": True,
                "file_size": file_size,
                "tables": table_info,
                "total_records": total_records,
                "total_tables": len(tables),
            }

        except Exception as e:
            return {"exists": True, "error": str(e)}

    def find_data_overlap(
        self, jsonl_analysis: Dict, db_analysis: Dict
    ) -> Dict[str, Any]:
        """Find overlapping data between JSONL and SQLite"""
        print("🔍 Analyzing data overlap...")

        overlap_analysis = {
            "jsonl_unique": 0,
            "db_unique": 0,
            "overlapping": 0,
            "total_unique": 0,
            "redundancy_ratio": 0.0,
            "overlapping_ids": [],
        }

        if not jsonl_analysis.get("exists") or not db_analysis.get("exists"):
            return overlap_analysis

        # Get capsule IDs from JSONL
        jsonl_ids = set(jsonl_analysis.get("capsule_ids", []))

        # Get capsule IDs from database
        db_ids = set()
        for table_name, table_info in db_analysis.get("tables", {}).items():
            if "capsule_ids" in table_info:
                db_ids.update(table_info["capsule_ids"])

        # Calculate overlaps
        overlapping = jsonl_ids.intersection(db_ids)
        jsonl_unique = jsonl_ids - db_ids
        db_unique = db_ids - jsonl_ids

        total_records = len(jsonl_ids) + len(db_ids)
        unique_records = len(jsonl_ids.union(db_ids))

        overlap_analysis.update(
            {
                "jsonl_unique": len(jsonl_unique),
                "db_unique": len(db_unique),
                "overlapping": len(overlapping),
                "total_unique": unique_records,
                "redundancy_ratio": (total_records - unique_records) / total_records
                if total_records > 0
                else 0,
                "overlapping_ids": list(overlapping)[:10],
            }
        )

        return overlap_analysis

    def generate_consolidation_plan(
        self, jsonl_analysis: Dict, db_analysis: Dict, overlap_analysis: Dict
    ) -> Dict[str, Any]:
        """Generate a plan for data consolidation"""
        print("📋 Generating consolidation plan...")

        plan = {
            "strategy": "unknown",
            "primary_storage": "database",
            "actions": [],
            "estimated_space_savings": 0,
            "backup_recommendations": [],
        }

        jsonl_size = jsonl_analysis.get("file_size", 0)
        db_size = db_analysis.get("file_size", 0)
        redundancy = overlap_analysis.get("redundancy_ratio", 0)

        if redundancy > 0.5:  # More than 50% overlap
            plan["strategy"] = "consolidate_to_database"
            plan["actions"] = [
                "Keep SQLite database as primary storage",
                "Create backup of JSONL file",
                "Migrate any unique JSONL data to database",
                "Archive or remove JSONL file after verification",
                "Update application to use database exclusively",
            ]
            plan["estimated_space_savings"] = int(
                jsonl_size * 0.8
            )  # Estimate 80% of JSONL can be removed

        elif redundancy > 0.2:  # 20-50% overlap
            plan["strategy"] = "hybrid_with_sync"
            plan["actions"] = [
                "Keep both storage systems",
                "Implement sync mechanism",
                "Use database for new data",
                "Keep JSONL for backup/archive",
                "Add data consistency checks",
            ]
            plan["estimated_space_savings"] = 0

        else:  # Less than 20% overlap
            plan["strategy"] = "keep_both"
            plan["actions"] = [
                "Keep both storage systems as they contain different data",
                "Clearly document what each storage system contains",
                "Consider unified API for data access",
                "Add monitoring for data growth",
            ]
            plan["estimated_space_savings"] = 0

        plan["backup_recommendations"] = [
            "Create full backup before any changes",
            "Test data migration with subset first",
            "Verify data integrity after migration",
            "Keep original files for at least 30 days",
        ]

        return plan

    def create_backup(self) -> Dict[str, Any]:
        """Create backups before consolidation"""
        print("💾 Creating data backups...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(f"data_backup_{timestamp}")
        backup_dir.mkdir(exist_ok=True)

        backup_results = {"backup_dir": str(backup_dir), "files_backed_up": []}

        try:
            # Backup JSONL file
            if self.jsonl_path.exists():
                backup_jsonl = backup_dir / f"capsule_chain_backup_{timestamp}.jsonl"
                import shutil

                shutil.copy2(self.jsonl_path, backup_jsonl)
                backup_results["files_backed_up"].append(str(backup_jsonl))
                print(f"✅ JSONL backed up to {backup_jsonl}")

            # Backup SQLite database
            if self.db_path.exists():
                backup_db = backup_dir / f"uatp_dev_backup_{timestamp}.db"
                import shutil

                shutil.copy2(self.db_path, backup_db)
                backup_results["files_backed_up"].append(str(backup_db))
                print(f"✅ Database backed up to {backup_db}")

            backup_results["success"] = True
            return backup_results

        except Exception as e:
            backup_results["success"] = False
            backup_results["error"] = str(e)
            return backup_results

    def run_analysis(self) -> Dict[str, Any]:
        """Run complete analysis"""
        print("🔬 UATP Data Storage Analysis")
        print("=" * 50)

        # Analyze both storage systems
        jsonl_analysis = self.analyze_jsonl_file()
        db_analysis = self.analyze_sqlite_db()

        # Find overlaps
        overlap_analysis = self.find_data_overlap(jsonl_analysis, db_analysis)

        # Generate plan
        consolidation_plan = self.generate_consolidation_plan(
            jsonl_analysis, db_analysis, overlap_analysis
        )

        return {
            "jsonl_analysis": jsonl_analysis,
            "db_analysis": db_analysis,
            "overlap_analysis": overlap_analysis,
            "consolidation_plan": consolidation_plan,
            "timestamp": datetime.now().isoformat(),
        }


def print_analysis_report(analysis: Dict[str, Any]):
    """Print formatted analysis report"""
    print("\n📊 ANALYSIS REPORT")
    print("=" * 50)

    # JSONL Analysis
    jsonl = analysis["jsonl_analysis"]
    if jsonl.get("exists"):
        print(f"📄 JSONL File (capsule_chain.jsonl):")
        print(f"   Size: {jsonl.get('file_size', 0):,} bytes")
        print(f"   Capsules: {jsonl.get('unique_capsules', 0)}")
        print(f"   Lines: {jsonl.get('line_count', 0)}")
    else:
        print("📄 JSONL File: Not found")

    # Database Analysis
    db = analysis["db_analysis"]
    if db.get("exists"):
        print(f"\n🗄️  SQLite Database (uatp_dev.db):")
        print(f"   Size: {db.get('file_size', 0):,} bytes")
        print(f"   Tables: {db.get('total_tables', 0)}")
        print(f"   Total Records: {db.get('total_records', 0)}")

        for table_name, table_info in db.get("tables", {}).items():
            print(f"   - {table_name}: {table_info.get('record_count', 0)} records")
    else:
        print("🗄️  SQLite Database: Not found")

    # Overlap Analysis
    overlap = analysis["overlap_analysis"]
    print(f"\n🔍 Data Overlap Analysis:")
    print(f"   JSONL unique: {overlap.get('jsonl_unique', 0)}")
    print(f"   Database unique: {overlap.get('db_unique', 0)}")
    print(f"   Overlapping: {overlap.get('overlapping', 0)}")
    print(f"   Redundancy ratio: {overlap.get('redundancy_ratio', 0):.1%}")

    # Consolidation Plan
    plan = analysis["consolidation_plan"]
    print(f"\n📋 Consolidation Recommendation:")
    print(f"   Strategy: {plan.get('strategy', 'unknown')}")
    print(f"   Primary storage: {plan.get('primary_storage', 'unknown')}")
    print(
        f"   Estimated space savings: {plan.get('estimated_space_savings', 0):,} bytes"
    )

    print(f"\n✅ Recommended Actions:")
    for i, action in enumerate(plan.get("actions", []), 1):
        print(f"   {i}. {action}")

    print(f"\n⚠️  Backup Recommendations:")
    for i, rec in enumerate(plan.get("backup_recommendations", []), 1):
        print(f"   {i}. {rec}")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="UATP Data Storage Consolidation")
    parser.add_argument(
        "--jsonl", default="capsule_chain.jsonl", help="JSONL file path"
    )
    parser.add_argument("--db", default="uatp_dev.db", help="SQLite database path")
    parser.add_argument(
        "--backup", action="store_true", help="Create backup before analysis"
    )
    parser.add_argument(
        "--execute", action="store_true", help="Execute consolidation plan"
    )

    args = parser.parse_args()

    analyzer = DataStorageAnalyzer(args.jsonl, args.db)

    # Create backup if requested
    if args.backup:
        backup_result = analyzer.create_backup()
        if backup_result.get("success"):
            print(f"\n✅ Backup created: {backup_result['backup_dir']}")
        else:
            print(f"\n❌ Backup failed: {backup_result.get('error')}")
            return

    # Run analysis
    analysis = analyzer.run_analysis()

    # Print report
    print_analysis_report(analysis)

    # Save analysis to file
    analysis_file = f"data_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(analysis_file, "w") as f:
        json.dump(analysis, f, indent=2)
    print(f"\n💾 Analysis saved to: {analysis_file}")

    if args.execute:
        print(
            f"\n⚠️  Execution mode not implemented yet. Please review the analysis first."
        )
        print(f"   Run with --backup to create backups before making changes.")


if __name__ == "__main__":
    main()
