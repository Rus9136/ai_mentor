#!/usr/bin/env python3
"""
Automatic monthly partition creation script.

This script creates partitions for the next N months for partitioned tables:
- test_attempts (partition key: started_at)
- learning_activities (partition key: activity_timestamp)

Usage:
    # Create partitions for next 3 months (default)
    python scripts/create_monthly_partitions.py

    # Create partitions for next 6 months
    python scripts/create_monthly_partitions.py --months 6

    # Dry run (just print SQL)
    python scripts/create_monthly_partitions.py --dry-run

Recommended cron setup (run on 1st of each month at 00:05):
    5 0 1 * * cd /path/to/backend && python scripts/create_monthly_partitions.py --months 3 >> /var/log/partitions.log 2>&1
"""
import argparse
import asyncio
import sys
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from sqlalchemy import text
from app.core.database import async_engine


# Partitioned tables configuration
PARTITIONED_TABLES = [
    {
        "table": "test_attempts",
        "partition_key": "started_at",
    },
    {
        "table": "learning_activities",
        "partition_key": "activity_timestamp",
    },
]


def get_partition_info(table: str, year: int, month: int) -> Tuple[str, str, str]:
    """
    Get partition name and date range for a given table and month.

    Returns:
        Tuple of (partition_name, start_date, end_date)
    """
    partition_name = f"{table}_{year}_{month:02d}"

    start_date = f"{year}-{month:02d}-01"

    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"

    return partition_name, start_date, end_date


def generate_partition_sql(table: str, year: int, month: int) -> str:
    """Generate SQL to create a partition."""
    partition_name, start_date, end_date = get_partition_info(table, year, month)

    return f"""
        CREATE TABLE IF NOT EXISTS {partition_name}
        PARTITION OF {table}
        FOR VALUES FROM ('{start_date}') TO ('{end_date}');
    """


async def check_partition_exists(conn, partition_name: str) -> bool:
    """Check if a partition table already exists."""
    result = await conn.execute(
        text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = :partition_name
            );
        """),
        {"partition_name": partition_name},
    )
    return result.scalar()


async def create_partitions(months_ahead: int = 3, dry_run: bool = False) -> List[str]:
    """
    Create partitions for the next N months.

    Args:
        months_ahead: Number of months to create partitions for
        dry_run: If True, only print SQL without executing

    Returns:
        List of created partition names
    """
    created_partitions = []
    today = date.today()

    async with async_engine.begin() as conn:
        for table_config in PARTITIONED_TABLES:
            table = table_config["table"]
            print(f"\n📊 Processing table: {table}")

            for i in range(months_ahead):
                target_date = today + relativedelta(months=i)
                year = target_date.year
                month = target_date.month

                partition_name, start_date, end_date = get_partition_info(
                    table, year, month
                )

                # Check if partition already exists
                exists = await check_partition_exists(conn, partition_name)

                if exists:
                    print(f"  ⏭️  {partition_name} already exists, skipping")
                    continue

                sql = generate_partition_sql(table, year, month)

                if dry_run:
                    print(f"  🔍 Would create: {partition_name}")
                    print(f"      Range: [{start_date}, {end_date})")
                    print(f"      SQL: {sql.strip()}")
                else:
                    print(f"  ✅ Creating: {partition_name}")
                    print(f"      Range: [{start_date}, {end_date})")
                    await conn.execute(text(sql))
                    created_partitions.append(partition_name)

    return created_partitions


async def list_existing_partitions() -> None:
    """List all existing partitions for partitioned tables."""
    async with async_engine.connect() as conn:
        for table_config in PARTITIONED_TABLES:
            table = table_config["table"]
            print(f"\n📊 Partitions for {table}:")

            result = await conn.execute(
                text("""
                    SELECT
                        c.relname AS partition_name,
                        pg_get_expr(c.relpartbound, c.oid) AS partition_range,
                        pg_size_pretty(pg_relation_size(c.oid)) AS size,
                        (SELECT COUNT(*) FROM pg_class WHERE relname = c.relname) as row_count
                    FROM pg_class p
                    JOIN pg_inherits i ON p.oid = i.inhparent
                    JOIN pg_class c ON i.inhrelid = c.oid
                    WHERE p.relname = :table
                    ORDER BY c.relname;
                """),
                {"table": table},
            )

            partitions = result.fetchall()

            if not partitions:
                print("  No partitions found")
            else:
                for partition in partitions:
                    print(
                        f"  📁 {partition.partition_name}: {partition.partition_range} (Size: {partition.size})"
                    )


async def main():
    parser = argparse.ArgumentParser(
        description="Create monthly partitions for partitioned tables"
    )
    parser.add_argument(
        "--months",
        type=int,
        default=3,
        help="Number of months ahead to create partitions (default: 3)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print SQL without executing",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing partitions and exit",
    )

    args = parser.parse_args()

    print("🗄️  Partition Management Script")
    print("=" * 50)

    if args.list:
        await list_existing_partitions()
        return

    print(f"Creating partitions for next {args.months} months")
    if args.dry_run:
        print("🔍 DRY RUN MODE - no changes will be made")

    created = await create_partitions(
        months_ahead=args.months,
        dry_run=args.dry_run,
    )

    print("\n" + "=" * 50)
    if args.dry_run:
        print(f"Would create {len(created)} new partitions")
    else:
        print(f"✅ Created {len(created)} new partitions")

    if created:
        print("New partitions:")
        for p in created:
            print(f"  - {p}")


if __name__ == "__main__":
    asyncio.run(main())
