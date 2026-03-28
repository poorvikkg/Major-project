import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="major_project",
    user="poorvik",
    password="poorvik123"
)

cursor = conn.cursor()