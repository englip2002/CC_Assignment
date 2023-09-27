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

from config import *
from pymysql import connections

bucket = custombucket
region = customregion

try:
    db_conn = connections.Connection(
        host=customhost,
        port=3306,
        user=customuser,
        password=custompass,
        db=customdb
    )
    print("Database connection success!")
except Exception as e:
    print("Database connection failed!")
    print(e)

# (('programme',), ('student',), ('company',), ('student_company',), ('supervisor',), ('cohort',), ('education_level',))
def main():
    sql=f'''
        DROP TABLE admin;
    '''
#     sql=f'''
#         SELECT table_name
# FROM information_schema.tables
# WHERE table_schema = '{customdb}'
# ;
#     '''
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