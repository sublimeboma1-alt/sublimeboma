#!/usr/bin/env python
"""Importe un dump MySQL Django dans la base configuree par Django.

Ce script est volontairement independant de l'application : il ne modifie ni
les modeles ni les migrations. Lancez d'abord les migrations PostgreSQL, puis
executez-le une seule fois avec DATABASE_PUBLIC_URL defini.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Iterator
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DUMP = ROOT / "sublime" / "backup_mysql.sql"
SKIPPED_TABLES = {
    "depense_categoriedepense",
    "django_migrations",
    "django_session",
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import MySQL dump into PostgreSQL")
    parser.add_argument("--dump", type=Path, default=DEFAULT_DUMP, help="Chemin du dump MySQL")
    parser.add_argument("--dry-run", action="store_true", help="Verifie le dump sans ecrire en base")
    parser.add_argument(
        "--allow-nonempty",
        action="store_true",
        help="Autorise l'import dans des tables contenant deja des donnees",
    )
    return parser.parse_args()


def source_columns(sql: str) -> dict[str, list[str]]:
    tables: dict[str, list[str]] = {}
    pattern = re.compile(r"CREATE TABLE `(?P<table>[^`]+)` \((?P<body>.*?)\) ENGINE=", re.DOTALL)
    for match in pattern.finditer(sql):
        columns = re.findall(r"^\s*`([^`]+)`", match.group("body"), re.MULTILINE)
        tables[match.group("table")] = columns
    return tables


def insert_statements(sql: str) -> Iterator[tuple[str, str]]:
    pattern = re.compile(r"INSERT INTO `(?P<table>[^`]+)` VALUES (?P<values>.*?);", re.DOTALL)
    for match in pattern.finditer(sql):
        yield match.group("table"), match.group("values")


def parse_values(values: str) -> list[list[object | None]]:
    """Parse les tuples VALUES produits par mysqldump, sans dependance MySQL."""
    rows: list[list[object | None]] = []
    row: list[object | None] = []
    token: list[str] = []
    quoted = False
    escaped = False
    in_row = False

    def append_value() -> None:
        raw = "".join(token).strip()
        token.clear()
        if raw.upper() == "NULL":
            row.append(None)
        elif raw in {"0", "1"}:
            row.append(int(raw))
        else:
            row.append(raw)

    index = 0
    while index < len(values):
        character = values[index]
        if quoted:
            if escaped:
                token.append({"0": "\0", "b": "\b", "n": "\n", "r": "\r", "t": "\t", "Z": "\x1a"}.get(character, character))
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == "'":
                quoted = False
            else:
                token.append(character)
        elif character == "'":
            quoted = True
        elif character == "(":
            if in_row:
                raise ValueError("Tuple MySQL imbrique non pris en charge")
            in_row = True
        elif character == "," and in_row:
            append_value()
        elif character == ")" and in_row:
            append_value()
            rows.append(row)
            row = []
            in_row = False
        elif in_row:
            token.append(character)
        index += 1

    if quoted or in_row:
        raise ValueError("Fin de dump inattendue pendant la lecture des valeurs")
    return rows


def main() -> int:
    arguments = parse_arguments()
    if not arguments.dump.is_file():
        print(f"Dump introuvable : {arguments.dump}", file=sys.stderr)
        return 2
    if not os.environ.get("DATABASE_PUBLIC_URL"):
        print("DATABASE_PUBLIC_URL doit contenir l'URL PostgreSQL.", file=sys.stderr)
        return 2

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sublime.settings")
    sys.path.insert(0, str(ROOT))
    import django

    django.setup()
    from django.db import connection, transaction

    if connection.vendor != "postgresql":
        print("La base cible doit etre PostgreSQL.", file=sys.stderr)
        return 2

    dump = arguments.dump.read_text(encoding="utf-8")
    columns_by_table = source_columns(dump)
    statements = list(insert_statements(dump))
    if not statements:
        print("Aucun INSERT MySQL detecte.", file=sys.stderr)
        return 2

    with connection.cursor() as cursor:
        database_tables = set(connection.introspection.table_names(cursor))

    imports = [(table, values) for table, values in statements if table not in SKIPPED_TABLES]
    missing_tables = sorted({table for table, _ in imports} - database_tables)
    if missing_tables:
        print("Tables absentes : " + ", ".join(missing_tables), file=sys.stderr)
        print("Executez d'abord : python manage.py migrate", file=sys.stderr)
        return 2

    target_columns: dict[str, list[str]] = {}
    with connection.cursor() as cursor:
        for table, _ in imports:
            target_columns[table] = [column.name for column in connection.introspection.get_table_description(cursor, table)]

    incompatible = {
        table: sorted(set(columns_by_table[table]) - set(target_columns[table]))
        for table, _ in imports
        if set(columns_by_table[table]) - set(target_columns[table])
    }
    if incompatible:
        print("Le schema PostgreSQL ne correspond pas au backup :", file=sys.stderr)
        for table, columns in incompatible.items():
            print(f"- {table} : colonnes absentes ({', '.join(columns)})", file=sys.stderr)
        return 2

    row_counts: dict[str, int] = {}
    for table, values in imports:
        rows = parse_values(values)
        if any(len(row) != len(columns_by_table[table]) for row in rows):
            print(f"Nombre de colonnes invalide dans {table}.", file=sys.stderr)
            return 2
        row_counts[table] = row_counts.get(table, 0) + len(rows)

    if arguments.dry_run:
        print("Verification terminee :")
        for table, count in row_counts.items():
            print(f"- {table}: {count} ligne(s)")
        print("Aucune donnee n'a ete ecrite.")
        return 0

    with transaction.atomic(), connection.cursor() as cursor:
        for table in row_counts:
            cursor.execute(f"SELECT COUNT(*) FROM {connection.ops.quote_name(table)}")
            if cursor.fetchone()[0] and not arguments.allow_nonempty:
                print(f"La table {table} contient deja des donnees. Import annule.", file=sys.stderr)
                print("Utilisez une base vide ou --allow-nonempty.", file=sys.stderr)
                return 2

        for table, values in imports:
            columns = columns_by_table[table]
            quoted_table = connection.ops.quote_name(table)
            quoted_columns = ", ".join(connection.ops.quote_name(column) for column in columns)
            placeholders = ", ".join(["%s"] * len(columns))
            query = f"INSERT INTO {quoted_table} ({quoted_columns}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
            cursor.executemany(query, parse_values(values))

        for table in row_counts:
            if "id" in target_columns[table]:
                quoted_table = connection.ops.quote_name(table)
                cursor.execute(
                    "SELECT setval(pg_get_serial_sequence(%s, 'id'), "
                    "COALESCE((SELECT MAX(id) FROM " + quoted_table + "), 1), true)",
                    [table],
                )

    print("Import termine :")
    for table, count in row_counts.items():
        print(f"- {table}: {count} ligne(s) lue(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
