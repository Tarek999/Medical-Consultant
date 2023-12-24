import mysql.connector


mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    auth_plugin='mysql_native_password',
    database="doctors_db"
)

mycursor = mydb.cursor()

mycursor.execute(
    "CREATE TABLE patients (name VARCHAR(255), address INT)")

patient_sql = "INSERT INTO patients (name, address) VALUES (%s, %s)"
patient_val = ('Choose patient from below', 120)

mycursor.execute(patient_sql, patient_val)


mycursor.execute(
    "CREATE TABLE doctors (name VARCHAR(255), type VARCHAR(255), address INT)")
    

sql = "INSERT INTO doctors (name, type, address) VALUES (%s, %s, %s)"
val = [
    ('Yasser', 'A', 1),
    ('Mostafa', 'A', 2),
    ('Hassan', 'B', 3),
    ('Anas', 'B', 4)
    
]
mycursor.executemany(sql, val)

mydb.commit()
