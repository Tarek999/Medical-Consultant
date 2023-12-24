import mysql.connector


mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    auth_plugin='mysql_native_password',
    database="doctors_db"
)

mycursor = mydb.cursor()


def Update(name, address):
    sql = "UPDATE doctors SET address = %s WHERE name = %s"
    val = (address, name)

    mycursor.execute(sql, val)
    mydb.commit()


def fetchAddress(name):
    sql = f"SELECT address FROM doctors WHERE name = %s"
    val = (name,)
    mycursor.execute(sql, val)

    myresult = mycursor.fetchone()

    return myresult


def GetAllDoctors():
    mycursor.execute("SELECT * FROM doctors")

    myresult = mycursor.fetchall()

    return myresult


def addPatient(name, address):
    sql = "INSERT INTO patients (name, address) VALUES (%s, %s)"
    val = (name,  address)
    mycursor.execute(sql, val)
    mydb.commit()



def GetAllPatients():
    mycursor.execute("SELECT * FROM patients")

    myresult = mycursor.fetchall()

    return myresult


def dropPatientByAddress(address):
    sql = "DELETE FROM patients WHERE address = %s"
    adr = (address, )
    mycursor.execute(sql, adr)
    mydb.commit()
    return print(f'Patient with address: {address} is deleted from the database')


def dropPatientByName(name):

    try:
        sql = "DELETE FROM patients WHERE name = %s"
        name = (name, )
        mycursor.execute(sql, name)
        mydb.commit()
        return print(f'Patient with name: {name} is deleted from the database')
    except print('SOMETHING WRONG'):
        pass


def dropAllPatients():
    sql = f"DELETE * FROM patients"
    mycursor.execute(sql)
    mydb.commit()
    return print(f'All patients are deleted from the database')
