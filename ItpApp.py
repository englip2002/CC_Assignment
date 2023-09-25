from flask import Flask, render_template, send_from_directory, request, redirect, url_for
from pymysql import connections
import os
import boto3
from config import *
import json

app = Flask(__name__)

bucket = custombucket
region = customregion

loginState = False
loginNric = ""
loginEmail = ""

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
    edulevelList = selectAllFromTable("education_level")
    cohortList = selectAllFromTable("cohort")
    programmeList = selectAllFromTable("programme")
    supervisorList = selectAllFromTable("supervisor")
    return render_template('signUp.html',
                           edulevelList=edulevelList,
                           cohortList=cohortList,
                           programmeList=json.dumps(programmeList),
                           supervisorList=supervisorList)
    # return render_template('signUp.html')

@app.route("/studentHomepage", methods=['GET', 'POST'])
def studentHomepage():
    return render_template('studentHomepage.html')

@app.route("/portfolio", methods=['GET', 'POST'])
def portfolio():
    return render_template('portfolio.html')

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
    # Personal Data
    profile_picture = request.form['profile_picture']
    name = request.form['name']
    nric = request.form['nric']
    gender = request.form['gender']
    transport = request.form['transport']
    health_remark = request.form['health_remark']

    # Academic Detail
    student_id = request.form['student_id']
    tutorial_group = request.form['tutorial_group']
    cgpa = request.form['cgpa']
    education_level = request.form['education_level']
    cohort = request.form['cohort']
    programme = request.form['programme']
    supervisor = request.form['supervisor']

    # Contact Information
    email = request.form['email']
    term_address = request.form['term_address']
    permanent_address = request.form['permanent_address']
    mobile_phone = request.form['mobile_phone']
    fixed_phone = request.form['fixed_phone']

    # Technical Knowledge
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
    except Exception as e:
        return str(e)
    
    try:    
        # Insert record to sql
        cursor = db_conn.cursor()
        insert_sql = f"INSERT INTO `student` (`id`, `profile_picture_url`, `name`, `nric`, `gender`, `transport`, `health_remark`, `student_id`, `tutorial_group`, `cgpa`, `education_level_id`, `cohort_id`, `programme_id`, `supervisor_id`, `email`, `term_address`, `permanent_address`, `mobile_phone`, `fixed_phone`, `programming_knowledge`, `database_knowledge`, `networking_knowledge`, `deleted`) VALUES (NULL, '{pfp_url}', '{name}', '{nric}', '{gender}', '{transport}', '{health_remark}', '{student_id}', '{tutorial_group}', '{cgpa}', '{education_level}', '{cohort}', '{programme}', '{supervisor}', '{email}', '{term_address}', '{permanent_address}', '{mobile_phone}', '{fixed_phone}', '{programming_knowledge}', '{database_knowledge}', '{networking_knowledge}', '0');"
        cursor.execute(insert_sql)
        db_conn.commit()
    except Exception as e:
        return str(e)
    finally:
        cursor.close()

    return redirect(url_for('home'))


@app.route("/login", methods=['GET', 'POST'])
def login():
    return render_template('login.html')


@app.route("/loginApi", methods=['POST'])
def loginApi():
    email = request.form['email']
    nric = request.form['nric']

    try:
        cursor = db_conn.cursor()
        cursor.execute("select student_id, email from student WHERE deleted=0")
        output = cursor.fetchall()
    except Exception as e:
        return str(e)
    finally:
        cursor.close()

    for each in output:
        if each[0] == nric and each[1] == email:
            loginState = True
            loginEmail = each[1]
            loginNric = each[0]
            return redirect(url_for('home'))

    return render_template('login.html', invalidLogin=True)

    

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
def adminHomepage():
    return render_template('adminHomepage.html', invalidLogin=True)

@app.route("/studentDetail", methods=["GET"])
def studentDetail():
    return render_template('studentDetail.html', invalidLogin=True)

if __name__ == '__main__':
    app.run(debug=True)
