from flask import Flask, render_template, send_from_directory, request, redirect, url_for
from pymysql import connections
import os
import boto3
from config import *
import json

app = Flask(__name__)

bucket = custombucket
region = customregion

global loginState, loginNric, loginEmail
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
    global loginState, loginNric, loginEmail

    if not loginState:
        return redirect(url_for('home'))
    
    try:
        cursor = db_conn.cursor()
        
        # Student Info
        cursor.execute(f'''
            SELECT `student`.*, `cohort`.`name` AS `cohort.name`, `cohort`.`period` AS `cohort.period`, `education_level`.`name` AS `education_level.name`, `programme`.`name` AS `programme.name`, `programme`.`code` AS `programme.code`, `supervisor`.`name` AS `supervisor.name`, `supervisor`.`email` AS `supervisor.email`
            FROM `student` 
                LEFT JOIN `cohort` ON `student`.`cohort_id` = `cohort`.`id` 
                LEFT JOIN `education_level` ON `student`.`education_level_id` = `education_level`.`id` 
                LEFT JOIN `programme` ON `student`.`programme_id` = `programme`.`id` 
                LEFT JOIN `supervisor` ON `student`.`supervisor_id` = `supervisor`.`id`
            WHERE `student`.`deleted`='0';
            ''')
        output = cursor.fetchall()
        
        # Student Table Columns
        cursor.execute(f"select column_name from information_schema.columns where table_name = N'student' and table_schema='{customdb}' order by ordinal_position")
        columns = cursor.fetchall()

        # Company Info
        cursor.execute(f'''
            SELECT student_company.*, company.*
            FROM student_company
                LEFT JOIN company ON student_company.company_id = company.id
            WHERE student_company.student_id = '{output[0][0]}' AND student_company.deleted = '0' AND company.deleted = '0';
            ''')
        companyOutput = cursor.fetchall()

        # Company columns
        cursor.execute(f"select column_name from information_schema.columns where table_name = N'student_company' and table_schema='{customdb}' order by ordinal_position")
        scColumns = cursor.fetchall()
        cursor.execute(f"select column_name from information_schema.columns where table_name = N'company' and table_schema='{customdb}' order by ordinal_position")
        cColumns = cursor.fetchall()
        
    except Exception as e:
        return str(e)
    finally:
        cursor.close()

    fColumns = list(map(lambda x: x[0], columns))
    fColumns.extend(["cohort_name", "cohort_period", "education_level_name", "programme_name", "programme_code", "supervisor_name", "supervisor_email"])
    
    fOutput = {}
    for i, each in enumerate(fColumns):
        fOutput[each] = output[0][i]

    companyInfo = {}
    tempColumns = list(scColumns)
    tempColumns.extend(list(cColumns))
    if len(companyOutput) > 0:
        for i, each in enumerate(tempColumns):
            companyInfo[each[0]] = companyOutput[0][i]
    else:
        for i, each in enumerate(tempColumns):
            companyInfo[each[0]] = "-"

    return render_template('studentHomepage.html', loginInfo=(loginState, loginNric, loginEmail), studInfo=fOutput, columns=fColumns, companyInfo=companyInfo)

@app.route("/registerCompany", methods=['GET', 'POST'])
def registerCompany():
    return render_template('registerCompany.html')

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

    return redirect(url_for('studentHomepage'))


@app.route("/login", methods=['GET', 'POST'])
def login():
    global loginState, loginNric, loginEmail

    if loginState:
        return redirect(url_for('studentHomepage'))
    
    return render_template('login.html')


@app.route("/loginApi", methods=['POST'])
def loginApi():
    email = request.form['email']
    nric = request.form['nric']

    try:
        cursor = db_conn.cursor()
        cursor.execute("select nric, email from student WHERE deleted=0")
        output = cursor.fetchall()
    except Exception as e:
        return str(e)
    finally:
        cursor.close()

    for each in output:
        if each[0] == nric and each[1] == email:
            global loginState, loginEmail, loginNric
            loginState = True
            loginEmail = each[1]
            loginNric = each[0]
            return redirect(url_for('studentHomepage'))

    return render_template('login.html', invalidLogin=True)


@app.route("/logoutApi", methods=['GET', 'POST'])
def logoutApi():
    global loginState, loginEmail, loginNric
    loginState = False
    loginEmail = ""
    loginNric = ""
    return redirect(url_for('home'))


global adminLoginState
adminLoginState = False

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
            global adminLoginState
            adminLoginState = True
            return redirect(url_for('adminPortal'))

    return render_template('adminLogin.html', invalidLogin=True)

@app.route("/adminLogoutApi", methods=["GET", "POST"])
def adminLogoutApi():
    global adminLoginState
    adminLoginState = False
    return redirect(url_for('home'))

@app.route("/adminPortal", methods=["GET"])
def adminHomepage():
    return render_template('adminHomepage.html', invalidLogin=True)

@app.route("/studentDetail", methods=["GET"])
def studentDetail():
    return render_template('studentDetail.html', invalidLogin=True)

if __name__ == '__main__':
    app.run(debug=True)
