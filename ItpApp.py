from flask import Flask, render_template, send_from_directory, request, redirect, url_for
from pymysql import connections
import os
import boto3
from config import *
import json

app = Flask(__name__)

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
except:
    print("Database connection failed!")


def selectAllFromTable(tableName):
    try:
        cursor = db_conn.cursor()
        cursor.execute("select * from " + tableName + " WHERE deleted=0")
        output = cursor.fetchall()
    except Exception as e:
        cursor.close()
        return str(e)
    finally:
        cursor.close()
    return output


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('index.html')

# Static routes


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)


@app.route("/signUp", methods=['GET', 'POST'])
def signUp():
    # edulevelList = selectAllFromTable("education_level")
    # cohortList = selectAllFromTable("cohort")
    # programmeList = selectAllFromTable("programme")
    # supervisorList = selectAllFromTable("supervisor")
    return render_template('signUp.html')
    # return render_template('signUp.html',
    #                        edulevelList=edulevelList,
    #                        cohortList=cohortList,
    #                        programmeList=json.dumps(programmeList),
    #                        supervisorList=supervisorList)

@app.route("/studentHomepage", methods=['GET', 'POST'])
def studentHomepage():
    return render_template('studentHomepage.html')

@app.route("/test", methods=["GET"])
def test():
    cursor = db_conn.cursor()
    cursor.execute("select * from supervisor")
    output = cursor.fetchall()
    cursor.close()

    print(output)
    print(type(output))
    return render_template('test.html', output=output)


@app.route("/signupApi", methods=['POST'])
def signupApi():
    profile_picture = request.form['profile_picture']
    student_id = request.form['student_id']
    tutorial_group = request.form['tutorial_group']
    cgpa = request.form['cgpa']
    education_level = request.form['education_level']
    cohort = request.form['cohort']
    programme = request.form['programme']
    supervisor = request.form['supervisor']
    programming_knowledge = request.form['programming_knowledge']
    database_knowledge = request.form['database_knowledge']
    networking_knowledge = request.form['networking_knowledge']

    # Upload image to S3 first
    try:
        pfp_filename_in_s3 = "pfp/" +  "pfp-" + str(student_id)

        s3 = boto3.resource('s3')
        s3.Bucket(custombucket).put_object(
            Key=pfp_filename_in_s3, Body=profile_picture)
        bucket_location = boto3.client(
            's3').get_bucket_location(Bucket=custombucket)
        s3_location = (bucket_location['LocationConstraint'])

        if s3_location is None:
            s3_location = ''
        else:
            s3_location = '-' + s3_location

        pfp_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
            s3_location,
            custombucket,
            pfp_filename_in_s3)

        # Insert record to sql
        cursor = db_conn.cursor()
        insert_sql = f"INSERT INTO `student` (`id`, `student_id`, `tutorial_group`, `cgpa`, `education_level_id`, `cohort_id`, `programme_id`, `supervisor_id`, `profile_picture_url`, `programming_knowledge`, `database_knowledge`, `networking_knowledge`, `deleted`) VALUES (NULL, '{student_id}', '{tutorial_group}', '{cgpa}', '{education_level}', '{cohort}', '{programme}', '{supervisor}', '{pfp_url}', '{programming_knowledge}', '{database_knowledge}', '{networking_knowledge}', '0')"
        cursor.execute(insert_sql)
        db_conn.commit()

    except Exception as e:
        return str(e)
    finally:
        cursor.close()

    return render_template('signUpComplete.html')


@app.route("/login", methods=['GET', 'POST'])
def login():
    return render_template('login.html')


@app.route("/loginApi", methods=['POST'])
def loginApi():
    ...
    # student_id = request.form['student_id']
    # password = request.form['password']
    # last_name = request.form['last_name']
    # pri_skill = request.form['pri_skill']
    # location = request.form['location']
    # emp_image_file = request.files['emp_image_file']

    # to fetch all information
    # fetch_query = "SELECT * FROM your_table"
    # db_cursor.execute(fetch_query)

    # student_info = db_cursor.fetchall()
    # for row in student_info:
    #     column_value = row["column2_name"]  # By column name
    #     print(column_value)

    # insert_sql = "INSERT INTO students VALUES (%s, %s)"
    # if emp_image_file.filename == "":
    #     return "Please select a file"

    # try:

    #     cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
    #     db_conn.commit()
    #     emp_name = "" + first_name + " " + last_name
    #     # Uplaod image file in S3 #
    #     emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
    #     s3 = boto3.resource('s3')

    #     try:
    #         print("Data inserted in MySQL RDS... uploading image to S3...")
    #         s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
    #         bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
    #         s3_location = (bucket_location['LocationConstraint'])

    #         if s3_location is None:
    #             s3_location = ''
    #         else:
    #             s3_location = '-' + s3_location

    #         object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
    #             s3_location,
    #             custombucket,
    #             emp_image_file_name_in_s3)

    #     except Exception as e:
    #         return str(e)

    # finally:
    #     cursor.close()

    # print("all modification done...")
    # return render_template('AddEmpOutput.html', name=emp_name)

@app.route("/adminLogin", methods=['GET'])
def adminLogin():
    return render_template('adminLogin.html')



@app.route("/adminLogin", methods=["POST"])
def adminLoginApi():
    username = request.form['username']
    password = request.form['passwordEncrypted']

    output = selectAllFromTable('admin')

    for each in output:
        if each[1] == username and each[2] == password:
            return redirect(url_for('adminPortal'))

    return render_template('adminLogin.html', invalidLogin=True)


@app.route("/adminPortal", methods=["GET"])
def adminPortal():
    return "NIAMABDUICBYUVA"

if __name__ == '__main__':
    app.run(debug=True)
