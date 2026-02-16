from api.settings import settings

conn = settings.get_db_connection()
cur = conn.cursor()

for table in ['part_template', 'part_template_field', 'part_template_field_enum']:
    cur.execute(f"""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = '{table}' 
        ORDER BY ordinal_position
    """)

    print(f"\n{table}:")
    for row in cur.fetchall():
        print(f"  {row[0]:25} {row[1]:25} nullable={row[2]}")

conn.close()
