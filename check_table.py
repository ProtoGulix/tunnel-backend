from api.settings import settings

conn = settings.get_db_connection()
cur = conn.cursor()

cur.execute("""
    SELECT column_name, data_type, is_nullable 
    FROM information_schema.columns 
    WHERE table_name = 'part_template' 
    ORDER BY ordinal_position
""")

print("Table part_template columns:")
for row in cur.fetchall():
    print(f"  {row[0]:20} {row[1]:20} nullable={row[2]}")

conn.close()
