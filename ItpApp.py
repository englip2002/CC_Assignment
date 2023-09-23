from flask import Flask, render_template, send_from_directory, request
from pymysql import connections
import os
import boto3
from config import *


app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb
)


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('index.html')

# Static routes
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)


@app.route("/login", methods=['GET', 'POST'])
def login():
    return render_template('login.html')


@app.route("/signUp", methods=['GET', 'POST'])
def signUp():
    return render_template('signUp.html')

@app.route("/test", methods=["GET"])
def test():
    cursor = db_conn.cursor()
    cursor.execute("select * from supervisor")
    output = cursor.fetchall()
    cursor.close()

    print (output)
    print(type(output))
    return render_template('test.html', output=output)


@app.route("/loginApi", methods=['POST'])
def loginApi():
    ...
    # student_id = request.form['student_id']
    # password = request.form['password']
    # last_name = request.form['last_name']
    # pri_skill = request.form['pri_skill']
    # location = request.form['location']
    # emp_image_file = request.files['emp_image_file']
    
    #to fetch all information
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

if __name__ == '__main__':
    app.run(debug=True)
