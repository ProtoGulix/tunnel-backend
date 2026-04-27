"""
db_backup.py - Sauvegarde de la base de données
================================================
Crée une sauvegarde SQL des tables spécifiées.

Usage:
    python db_backup.py                    # Backup complet
    python db_backup.py --tables table1 table2  # Tables spécifiques
    python db_backup.py --output backup.sql     # Fichier de sortie
"""

import argparse
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

from db_connection import get_cursor, get_dict_cursor, get_connection, get_connection_params


def get_all_tables() -> list[str]:
    """Récupère la liste de toutes les tables du schéma public."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        return [row[0] for row in cursor.fetchall()]


def get_table_columns(table_name: str) -> list[str]:
    """Récupère les colonnes d'une table."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        return [row[0] for row in cursor.fetchall()]


def escape_value(value) -> str:
    """Échappe une valeur pour SQL."""
    if value is None:
        return 'NULL'
    if isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict) or isinstance(value, list):
        import json
        return "'" + json.dumps(value).replace("'", "''") + "'::jsonb"
    # String
    return "'" + str(value).replace("'", "''") + "'"


def backup_table(table_name: str) -> str:
    """Génère les instructions INSERT pour une table."""
    columns = get_table_columns(table_name)
    if not columns:
        return f"-- Table {table_name}: aucune colonne trouvée\n"
    
    lines = []
    lines.append(f"\n-- Table: {table_name}")
    lines.append(f"-- Backup généré le {datetime.now().isoformat()}")
    
    with get_dict_cursor() as cursor:
        cursor.execute(f'SELECT * FROM public."{table_name}"')
        rows = cursor.fetchall()
        
        if not rows:
            lines.append(f"-- (aucune donnée)")
            return "\n".join(lines)
        
        lines.append(f"-- {len(rows)} enregistrements")
        
        col_list = ', '.join(f'"{c}"' for c in columns)
        
        for row in rows:
            values = ', '.join(escape_value(row.get(col)) for col in columns)
            lines.append(f'INSERT INTO public."{table_name}" ({col_list}) VALUES ({values});')
    
    return "\n".join(lines)


def get_table_definition(table_name: str) -> str:
    """Génère la commande CREATE TABLE pour une table."""
    with get_cursor() as cursor:
        # Récupérer les colonnes avec leurs types et contraintes
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                is_nullable,
                column_default,
                udt_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = cursor.fetchall()
        if not columns:
            return f"-- Table {table_name}: aucune colonne trouvée\n"
        
        # Récupérer les contraintes PRIMARY KEY
        cursor.execute("""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = %s::regclass AND i.indisprimary
        """, (f'public.{table_name}',))
        
        pk_columns = [row[0] for row in cursor.fetchall()]
        
        # Récupérer les contraintes UNIQUE
        cursor.execute("""
            SELECT
                tc.constraint_name,
                string_agg(kcu.column_name, ', ' ORDER BY kcu.ordinal_position)
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'UNIQUE'
                AND tc.table_schema = 'public'
                AND tc.table_name = %s
            GROUP BY tc.constraint_name
        """, (table_name,))
        
        unique_constraints = cursor.fetchall()
        
        # Construire le CREATE TABLE
        lines = [f'CREATE TABLE IF NOT EXISTS public."{table_name}" (']
        
        col_definitions = []
        for col in columns:
            col_name = col[0]
            data_type = col[1]
            char_length = col[2]
            num_precision = col[3]
            num_scale = col[4]
            is_nullable = col[5]
            col_default = col[6]
            udt_name = col[7]
            
            # Type de données
            if data_type == 'character varying':
                type_str = f'VARCHAR({char_length})' if char_length else 'VARCHAR'
            elif data_type == 'character':
                type_str = f'CHAR({char_length})'
            elif data_type == 'numeric' and num_precision:
                if num_scale:
                    type_str = f'NUMERIC({num_precision},{num_scale})'
                else:
                    type_str = f'NUMERIC({num_precision})'
            elif data_type == 'ARRAY':
                type_str = udt_name.replace('_', '') + '[]'
            elif data_type == 'USER-DEFINED':
                type_str = udt_name
            else:
                type_str = data_type.upper()
            
            col_def = f'    "{col_name}" {type_str}'
            
            # NOT NULL
            if is_nullable == 'NO':
                col_def += ' NOT NULL'
            
            # DEFAULT
            if col_default:
                col_def += f' DEFAULT {col_default}'
            
            col_definitions.append(col_def)
        
        lines.append(',\n'.join(col_definitions))
        
        # PRIMARY KEY
        if pk_columns:
            pk_cols = ', '.join(f'"{col}"' for col in pk_columns)
            lines.append(f',\n    PRIMARY KEY ({pk_cols})')
        
        # UNIQUE constraints
        for constraint_name, columns_str in unique_constraints:
            lines.append(f',\n    CONSTRAINT "{constraint_name}" UNIQUE ({columns_str})')
        
        lines.append(');')
        
        return '\n'.join(lines)


def backup_schema() -> str:
    """Génère le schéma des tables (CREATE TABLE)."""
    lines = []
    lines.append("-- ===========================================")
    lines.append("-- SCHEMA BACKUP")
    lines.append(f"-- Généré le {datetime.now().isoformat()}")
    lines.append("-- ===========================================")
    
    with get_cursor() as cursor:
        # Récupérer les définitions des tables
        cursor.execute("""
            SELECT 
                'CREATE TABLE IF NOT EXISTS public."' || tablename || '" ();' as create_stmt
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        # Note: Pour un vrai schéma, il faudrait pg_dump ou une requête plus complexe
    
    return "\n".join(lines)


def full_backup_pgdump(output_file: str = None, tables: list[str] = None) -> str:
    """
    Effectue une sauvegarde complète avec pg_dump (schéma + données).
    
    Args:
        output_file: Fichier de sortie (None = auto-généré)
        tables: Liste des tables à sauvegarder (None = toutes)
    """
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"backup_{timestamp}.sql"
    
    output_path = Path(__file__).parent.parent / output_file
    
    params = get_connection_params()
    
    # Construire la commande pg_dump
    cmd = [
        'pg_dump',
        '-h', params['host'],
        '-p', str(params['port']),
        '-U', params['user'],
        '-d', params['dbname'],
        '--no-owner',
        '--no-acl',
        '-f', str(output_path)
    ]
    
    # Ajouter les tables spécifiques si demandé
    if tables:
        for table in tables:
            cmd.extend(['-t', f'public.{table}'])
        print(f"Sauvegarde de {len(tables)} tables avec pg_dump...")
    else:
        print(f"Sauvegarde complète de la base avec pg_dump...")
    
    # Configurer l'environnement pour le mot de passe
    env = os.environ.copy()
    env['PGPASSWORD'] = params['password']
    
    try:
        # Exécuter pg_dump
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        file_size = output_path.stat().st_size
        print(f"\n✓ Sauvegarde créée: {output_path}")
        print(f"  Taille: {file_size:,} octets")
        
        return str(output_path)
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Erreur lors du backup:")
        print(f"  {e.stderr}")
        raise
    except FileNotFoundError:
        print("✗ Erreur: pg_dump n'est pas trouvé dans le PATH")
        print("  Installez PostgreSQL client ou ajoutez pg_dump au PATH")
        print("  Fallback vers le backup Python...")
        return full_backup_python(tables, output_file)


def full_backup_python(tables: list[str] = None, output_file: str = None) -> str:
    """
    Effectue une sauvegarde avec Python (schéma + données).
    
    Args:
        tables: Liste des tables à sauvegarder (None = toutes)
        output_file: Fichier de sortie (None = auto-généré)
    """
    if tables is None:
        tables = get_all_tables()
    
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"backup_{timestamp}.sql"
    
    print(f"Sauvegarde de {len(tables)} tables...")
    
    content = []
    content.append("-- ===========================================")
    content.append("-- DATABASE BACKUP (Python)")
    content.append(f"-- Généré le {datetime.now().isoformat()}")
    content.append(f"-- Tables: {len(tables)}")
    content.append("-- ===========================================")
    content.append("")
    content.append("BEGIN;")
    content.append("")
    
    # Générer les CREATE TABLE
    content.append("-- ===========================================")
    content.append("-- SCHEMA (CREATE TABLE)")
    content.append("-- ===========================================")
    content.append("")
    
    for i, table in enumerate(tables, 1):
        print(f"  [{i}/{len(tables)}] Schéma de {table}...")
        content.append(f"-- Table: {table}")
        content.append(get_table_definition(table))
        content.append("")
    
    # Générer les INSERT
    content.append("")
    content.append("-- ===========================================")
    content.append("-- DONNÉES (INSERT)")
    content.append("-- ===========================================")
    content.append("")
    
    for i, table in enumerate(tables, 1):
        print(f"  [{i}/{len(tables)}] Données de {table}...")
        content.append(backup_table(table))
    
    content.append("")
    content.append("COMMIT;")
    
    full_content = "\n".join(content)
    
    # Écrire le fichier
    output_path = Path(__file__).parent.parent / output_file
    output_path.write_text(full_content, encoding='utf-8')
    
    print(f"\n✓ Sauvegarde créée: {output_path}")
    print(f"  Taille: {len(full_content):,} octets")
    
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(description='Sauvegarde de la base de données')
    parser.add_argument('--tables', '-t', nargs='+', help='Tables à sauvegarder')
    parser.add_argument('--output', '-o', help='Fichier de sortie')
    parser.add_argument('--list', '-l', action='store_true', help='Lister les tables')
    parser.add_argument('--python', '-p', action='store_true', help='Utiliser le backup Python (données uniquement)')
    
    args = parser.parse_args()
    
    if args.list:
        tables = get_all_tables()
        print(f"\nTables disponibles ({len(tables)}):")
        for t in tables:
            print(f"  - {t}")
        return
    
    if args.python:
        full_backup_python(tables=args.tables, output_file=args.output)
    else:
        full_backup_pgdump(output_file=args.output, tables=args.tables)


if __name__ == "__main__":
    main()
