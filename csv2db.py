import csv
import psycopg2


DB_NAME = "foundation"
DB_USER = "wilson"
DB_PASSWORD = "qwert"
DB_HOST = "localhost"
DB_PORT = "5432"




conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)


cur = conn.cursor()


cur.execute("""
CREATE TABLE IF NOT EXISTS cosmetics (
    id SERIAL PRIMARY KEY,
    brand VARCHAR(255),
    name VARCHAR(255),
    type VARCHAR(255),
    color VARCHAR(50)
)
""")

cur = conn.cursor()

# insert csv file into db
with open('items.csv', 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    next(reader)  
    i = 1
    for row in reader:
        brand, name, type_, color, _ = row  
        #print(row)
        
        cur.execute(
            "INSERT INTO items ( id ,brand, name, type, color) VALUES (%s ,%s, %s, %s, %s)",
            (i, brand, name, type_, color)
        )
        i = i+1


conn.commit()
cur.close()
conn.close()