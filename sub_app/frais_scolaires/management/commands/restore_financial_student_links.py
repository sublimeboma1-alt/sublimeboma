"""Restaure les liens eleve des frais et paiements depuis un dump MySQL."""

from __future__ import annotations

import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from sub_app.eleves.models import Eleve
from sub_app.frais_scolaires.models import FraisScolaire, Paiement


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DUMP = ROOT / 'backup_mysql (1).sql'
TABLES = {
    'frais_scolaires_fraisscolaire': FraisScolaire,
    'frais_scolaires_paiement': Paiement,
}


def source_columns(sql: str) -> dict[str, list[str]]:
    tables = {}
    pattern = re.compile(r'CREATE TABLE `(?P<table>[^`]+)` \((?P<body>.*?)\) ENGINE=', re.DOTALL)
    for match in pattern.finditer(sql):
        tables[match.group('table')] = re.findall(r'^\s*`([^`]+)`', match.group('body'), re.MULTILINE)
    return tables


def insert_values(sql: str, table: str) -> list[str]:
    pattern = re.compile(rf'INSERT INTO `{re.escape(table)}` VALUES (?P<values>.*?);', re.DOTALL)
    return [match.group('values') for match in pattern.finditer(sql)]


def parse_rows(values: str) -> list[list[object | None]]:
    rows, row, token = [], [], []
    quoted = escaped = in_row = False

    def append_value() -> None:
        raw = ''.join(token).strip()
        token.clear()
        row.append(None if raw.upper() == 'NULL' else raw)

    for character in values:
        if quoted:
            if escaped:
                token.append({'0': '\0', 'b': '\b', 'n': '\n', 'r': '\r', 't': '\t', 'Z': '\x1a'}.get(character, character))
                escaped = False
            elif character == '\\':
                escaped = True
            elif character == "'":
                quoted = False
            else:
                token.append(character)
        elif character == "'":
            quoted = True
        elif character == '(':
            in_row = True
        elif character == ',' and in_row:
            append_value()
        elif character == ')' and in_row:
            append_value()
            rows.append(row)
            row = []
            in_row = False
        elif in_row:
            token.append(character)
    if quoted or in_row:
        raise ValueError('Fin de dump inattendue.')
    return rows


def student_links(sql: str, table: str) -> dict[int, int]:
    columns = source_columns(sql).get(table)
    if not columns or 'id' not in columns or 'eleve_id' not in columns:
        raise ValueError(f'Les colonnes id et eleve_id sont introuvables dans {table}.')
    id_index, eleve_index = columns.index('id'), columns.index('eleve_id')
    links = {}
    for values in insert_values(sql, table):
        for row in parse_rows(values):
            if len(row) != len(columns):
                raise ValueError(f'Nombre de colonnes invalide dans {table}.')
            if row[eleve_index] is not None:
                links[int(row[id_index])] = int(row[eleve_index])
    return links


class Command(BaseCommand):
    help = 'Restaure les liens eleve manquants des frais et paiements depuis un dump MySQL.'

    def add_arguments(self, parser):
        parser.add_argument('--dump', type=Path, default=DEFAULT_DUMP, help='Chemin du dump MySQL source.')
        parser.add_argument('--apply', action='store_true', help='Applique la restauration. Sans cette option, aucun changement n’est fait.')

    def handle(self, *args, **options):
        dump_path = options['dump']
        if not dump_path.is_file():
            raise CommandError(f'Dump introuvable : {dump_path}')
        try:
            sql = dump_path.read_text(encoding='utf-8')
            links_by_table = {table: student_links(sql, table) for table in TABLES}
        except (OSError, UnicodeDecodeError, ValueError) as error:
            raise CommandError(f'Lecture du dump impossible : {error}') from error

        existing_students = set(Eleve.objects.filter(id__in={student_id for links in links_by_table.values() for student_id in links.values()}).values_list('id', flat=True))
        summaries = []
        for table, model in TABLES.items():
            links = links_by_table[table]
            current = dict(model.objects.filter(id__in=links).values_list('id', 'eleve_id'))
            restorable = {row_id: student_id for row_id, student_id in links.items() if current.get(row_id) is None and student_id in existing_students}
            summaries.append((model, table, links, current, restorable))
            self.stdout.write(
                f'{table} : {len(links)} lien(s) dans le dump, {len(restorable)} lien(s) a restaurer, '
                f'{sum(row_id not in current for row_id in links)} ligne(s) absente(s) de la base actuelle.'
            )

        if not options['apply']:
            self.stdout.write(self.style.WARNING('Mode apercu : aucune donnee n’a ete modifiee. Relancez avec --apply pour restaurer.'))
            return

        updated = {}
        with transaction.atomic():
            for model, table, _links, _current, restorable in summaries:
                count = 0
                for row_id, student_id in restorable.items():
                    count += model.objects.filter(id=row_id, eleve__isnull=True).update(eleve_id=student_id)
                updated[table] = count
        self.stdout.write(self.style.SUCCESS(
            'Restauration terminee : ' + ', '.join(f'{table}={count}' for table, count in updated.items())
        ))
