import csv
import psycopg2

# PostgreSQL数据库连接参数
DB_NAME = "foundation"
DB_USER = "wilson"
DB_PASSWORD = "qwert"
DB_HOST = "localhost"
DB_PORT = "5432"



# 连接到PostgreSQL数据库
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)

# 创建游标对象
cur = conn.cursor()

# 创建表格
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

# 读取CSV文件并插入数据到数据库的items表格
with open('cosmetics.csv', 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    next(reader)  # 跳过标题行
    for row in reader:
        brand, name, type_, color, _ = row  # 忽略'makeup'列
        cur.execute(
            "INSERT INTO items (brand, name, type, color) VALUES (%s, %s, %s, %s)",
            (brand, name, type_, color)
        )

# 提交事务
conn.commit()

# 关闭游标和连接
cur.close()
conn.close()