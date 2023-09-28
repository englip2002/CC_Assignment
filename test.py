# field = [
#     [1, 1, 0, 0, 1],
#     [0, 0, 1, 0, 1],
#     [1, 0, 0, 1, 0],
#     [0, 1, 0, 1, 0],
#     [1, 0, 1, 0, 0],
# ]

# pos = [0, 0]
# actions = ['upLeft', 'up', 'upRight', 'left', 'center', 'right', 'downLeft', 'down', 'downRight']

# solutionPath = []

# def isGoal(thisPos):
#     return thisPos[0] == len(field) - 1

# def findSafeSpaces(thisPos):
#     output = []
#     for i, a in enumerate(actions):
#         tempPos = [-1 + (i % 3) + thisPos[0], -1 + int((i) / 3) + thisPos[1]]
#         if (tempPos[0] >= 0 and tempPos[0] < len(field) and tempPos[1] >= 0 and tempPos[1] < len(field[0])):
#             output.append({'action': a, 'pos': tempPos})
#     return output

# while (not isGoal(pos)):
#     safeSpaces = findSafeSpaces
#     for each in safeSpaces:
#         ...
# print(findSafeSpaces([0,0]))

# import hashlib
# def hash_plaintext(plaintext, salt):
#     # Concatenate the salt and plaintext
#     salted_password = salt + plaintext

#     # Create a new SHA-256 hash object
#     sha256 = hashlib.sha256()

#     # Update the hash object with the salted password bytes
#     sha256.update(salted_password.encode('utf-8'))

#     # Get the hexadecimal representation of the hash
#     hashed_password = sha256.hexdigest()

#     return hashed_password

# def hash_student_nric(nric):
#     return hash_plaintext(nric, 'cc~ASSignment_AWS=nr1c')

# def hash_admin_password(password):
#     return hash_plaintext(password, 'AWS_admin-CC~assignment')


# print(hash_student_nric('123456-12-1234'))

from config import *
from pymysql import connections

bucket = custombucket
region = customregion

try:
    db_conn = connections.Connection(
        host='database-try1.chidbtnhv9jm.us-east-1.rds.amazonaws.com',
        port=3306,
        user='admin',
        password='admin123',
        db=customdb
    )
    print("Database connection success!")
except Exception as e:
    print("Database connection failed!")
    print(e)

# (('programme',), ('student',), ('company',), ('student_company',), ('supervisor',), ('cohort',), ('education_level',))
def main():
    sql = "SELECT * FROM student"
    output = sql
    try:
        # Insert record to sql
        cursor = db_conn.cursor()

        print("Executing SQL")
        cursor.execute(sql)

        print("Comitting SQL")
        # db_conn.commit()
        output = cursor.fetchall()

    except Exception as e:
        return "Exception at SQL: " + str(e)
    finally:
        cursor.close()

    print("Done!")
    return str(output)

x = main()
print(x)