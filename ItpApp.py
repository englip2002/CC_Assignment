from flask import Flask, render_template, send_from_directory, request, redirect, url_for, session
from pymysql import connections
from datetime import datetime
import boto3
from config import *
import json
from functools import wraps
import hashlib

app = Flask(__name__)
app.secret_key = "b148f8d1e53eb3b4378f5c7438335965"     # 16 byte secret key

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

def requireStudentLogin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login', notLoggedInWarning = True))
        return f(*args, **kwargs)
    return decorated_function


def requireAdminLogin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('adminLogin', notLoggedInWarning = True))
        return f(*args, **kwargs)
    return decorated_function

def hash_plaintext(plaintext, salt):
    # Concatenate the salt and plaintext
    salted_password = salt + plaintext

    # Create a new SHA-256 hash object
    sha256 = hashlib.sha256()

    # Update the hash object with the salted password bytes
    sha256.update(salted_password.encode('utf-8'))

    # Get the hexadecimal representation of the hash
    hashed_password = sha256.hexdigest()

    return hashed_password

def hash_admin_password(password):
    return hash_plaintext(password, 'AWS_admin-CC~assignment')


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('index.html')

# Static routes
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

@app.route("/signUp", methods=['GET', 'POST'])
def signUp():
    if session.get('logged_in'):
        return redirect(url_for('studentHomepage'))
    
    
    recordAlreadyExist = request.args.get('recordAlreadyExist')
    
    edulevelList = selectAllFromTable("education_level")
    cohortList = selectAllFromTable("cohort")
    programmeList = selectAllFromTable("programme")
    supervisorList = selectAllFromTable("supervisor")
    return render_template('signUp.html',
                           edulevelList=edulevelList,
                           cohortList=cohortList,
                           programmeList=json.dumps(programmeList),
                           supervisorList=supervisorList, 
                           recordAlreadyExist=recordAlreadyExist)


@app.route("/signupApi", methods=['POST'])
def signupApi():
    # Personal Data
    profile_picture = request.files['profile_picture']
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

    # Check if record already exist
    try:
        # Insert record to sql
        cursor = db_conn.cursor()
        cursor.execute(f"SELECT * FROM student WHERE deleted='0' AND nric='{nric}' AND email='{email}'")
        recordExist = cursor.fetchone()
    except Exception as e:
        return "Exception at SQL: " + str(e)
    finally:
        cursor.close()
    if recordExist != None:
        return redirect(url_for('signup', recordAlreadyExist=True))

    # Upload image to S3 first
    pfp_url = ""
    try:
        pfp_filename_in_s3 = "pfp/" + "pfp-" + str(student_id)

        s3 = boto3.resource('s3')

        s3.Bucket(custombucket).put_object(
            Key=pfp_filename_in_s3, Body=profile_picture, ContentType=profile_picture.content_type)
        
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
        return "Exception at profile_picture: " + str(e)

    try:
        # Insert record to sql
        cursor = db_conn.cursor()
        insert_sql = f"INSERT INTO `student` (`id`, `profile_picture_url`, `name`, `nric`, `gender`, `transport`, `health_remark`, `student_id`, `tutorial_group`, `cgpa`, `education_level_id`, `cohort_id`, `programme_id`, `supervisor_id`, `email`, `term_address`, `permanent_address`, `mobile_phone`, `fixed_phone`, `programming_knowledge`, `database_knowledge`, `networking_knowledge`, `deleted`) VALUES (NULL, '{pfp_url}', '{name}', '{nric}', '{gender}', '{transport}', '{health_remark}', '{student_id}', '{tutorial_group}', '{cgpa}', '{education_level}', '{cohort}', '{programme}', '{supervisor}', '{email}', '{term_address}', '{permanent_address}', '{mobile_phone}', '{fixed_phone}', '{programming_knowledge}', '{database_knowledge}', '{networking_knowledge}', '0');"
        cursor.execute(insert_sql)
        db_conn.commit()
    except Exception as e:
        return "Exception at SQL: " + str(e)
    finally:
        cursor.close()

    session['logged_in'] = True
    session['email'] = email
    session['nric'] = nric

    return redirect(url_for('studentHomepage', signUpSuccess=True))


@app.route("/studentHomepage", methods=['GET', 'POST'])
@requireStudentLogin
def studentHomepage():

    signUpSuccess = request.args.get('signUpSuccess')
    updateSuccessParam = request.args.get('updateSuccess')

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
            WHERE `student`.`deleted`='0'
                AND `student`.`email` = '{session.get('email')}' 
                AND `student`.`nric` = '{session.get('nric')}';
            ''')
        output = cursor.fetchall()

        # Student Table Columns
        cursor.execute(
            f"select column_name from information_schema.columns where table_name = N'student' and table_schema='{customdb}' order by ordinal_position")
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
        cursor.execute(
            f"select column_name from information_schema.columns where table_name = N'student_company' and table_schema='{customdb}' order by ordinal_position")
        scColumns = cursor.fetchall()
        cursor.execute(
            f"select column_name from information_schema.columns where table_name = N'company' and table_schema='{customdb}' order by ordinal_position")
        cColumns = cursor.fetchall()

    except Exception as e:
        return str(e)
    finally:
        cursor.close()

    fColumns = list(map(lambda x: x[0], columns))
    fColumns.extend(["cohort_name", "cohort_period", "education_level_name",
                    "programme_name", "programme_code", "supervisor_name", "supervisor_email"])

    fOutput = {}
    for i, each in enumerate(fColumns):
        fOutput[each] = output[0][i]

    companyInfo = False
    if len(companyOutput) > 0:
        companyInfo = {}
        tempColumns = list(scColumns)
        tempColumns.extend(list(cColumns))
        for i, each in enumerate(tempColumns):
            companyInfo[each[0]] = companyOutput[0][i]

    return render_template('studentHomepage.html', studInfo=fOutput, companyInfo=companyInfo, updateSuccess=updateSuccessParam, signUpSuccess=signUpSuccess)


@app.route("/editPortfolio", methods=['GET', 'POST'])
@requireStudentLogin
def editPortfolio():

    edulevelList = selectAllFromTable("education_level")
    cohortList = selectAllFromTable("cohort")
    programmeList = selectAllFromTable("programme")
    supervisorList = selectAllFromTable("supervisor")

    try:
        # Insert record to sql
        cursor = db_conn.cursor()
        cursor.execute(
            f"SELECT * FROM student WHERE nric='{session.get('nric')}' AND email='{session.get('email')}' AND deleted='0';")
        output = cursor.fetchall()
        if len(output) == 0:
            return "Student Information not found!"

        # Student Table Columns
        cursor.execute(
            f"select column_name from information_schema.columns where table_name = N'student' and table_schema='{customdb}' order by ordinal_position")
        studentColumns = cursor.fetchall()

    except Exception as e:
        return str(e)
    finally:
        cursor.close()

    studentInfo = {}
    for i, col in enumerate(studentColumns):
        studentInfo[col[0]] = output[0][i]

    studentInfo['education_level_name'] = [i[1]
                                           for i in edulevelList if i[0] == studentInfo['education_level_id']][0]
    studentInfo['cohort_name'], studentInfo['cohort_period'] = [
        (i[1], i[2]) for i in cohortList if i[0] == studentInfo['cohort_id']][0]
    studentInfo['programme_name'], studentInfo['programme_code'] = [
        (i[1], i[2]) for i in programmeList if i[0] == studentInfo['programme_id']][0]
    studentInfo['supervisor_name'], studentInfo['supervisor_email'] = [
        (i[1], i[2]) for i in supervisorList if i[0] == studentInfo['supervisor_id']][0]

    return render_template('editPortfolio.html',
                           edulevelList=edulevelList,
                           cohortList=cohortList,
                           programmeList=programmeList,
                           programmeListJson=json.dumps(programmeList),
                           supervisorList=supervisorList,
                           studentInfo=studentInfo)


@app.route("/editPortfolioApi", methods=['POST'])
@requireStudentLogin
def editPortfolioApi():

    # Personal Data
    profile_picture = request.files['profile_picture']
    student_id = request.form['student_id']

    # If user updated profile pic
    pfp_url = ""
    if (profile_picture):
        # Upload picture to s3
        try:
            pfp_filename_in_s3 = "pfp/" + "pfp-" + str(student_id)

            s3 = boto3.resource('s3')
            s3.Bucket(custombucket).put_object(
                Key=pfp_filename_in_s3, Body=profile_picture, ContentType=profile_picture.content_type)
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

    # Update SQL
    try:
        cursor = db_conn.cursor()
        insert_sql = ""
        if (profile_picture and len(pfp_url) > 0):
            insert_sql = f'''
UPDATE `student` 
SET `profile_picture_url`='{pfp_url}', `name` = '{request.form['name']}', `gender` = '{request.form['gender']}', `transport` = '{request.form['transport']}', `health_remark` = '{request.form['health_remark']}', `student_id` = '{request.form['student_id']}', `tutorial_group` = '{request.form['tutorial_group']}', `cgpa` = '{request.form['cgpa']}', `education_level_id` = '{request.form['education_level']}', `cohort_id` = '{request.form['cohort']}', `programme_id` = '{request.form['programme']}', `supervisor_id` = '{request.form['supervisor']}', `term_address` = '{request.form['term_address']}', `permanent_address` = '{request.form['permanent_address']}', `mobile_phone` = '{request.form['mobile_phone']}', `fixed_phone` = '{request.form['fixed_phone']}', `programming_knowledge` = '{request.form['programming_knowledge']}', `database_knowledge` = '{request.form['database_knowledge']}', `networking_knowledge` = '{request.form['networking_knowledge']}' 
WHERE `student`.`email` = '{session.get('email')}' AND `student`.`nric` = '{session.get('nric')}';'''
        else:
            insert_sql = f'''
UPDATE `student` 
SET `name` = '{request.form['name']}', `gender` = '{request.form['gender']}', `transport` = '{request.form['transport']}', `health_remark` = '{request.form['health_remark']}', `student_id` = '{request.form['student_id']}', `tutorial_group` = '{request.form['tutorial_group']}', `cgpa` = '{request.form['cgpa']}', `education_level_id` = '{request.form['education_level']}', `cohort_id` = '{request.form['cohort']}', `programme_id` = '{request.form['programme']}', `supervisor_id` = '{request.form['supervisor']}', `term_address` = '{request.form['term_address']}', `permanent_address` = '{request.form['permanent_address']}', `mobile_phone` = '{request.form['mobile_phone']}', `fixed_phone` = '{request.form['fixed_phone']}', `programming_knowledge` = '{request.form['programming_knowledge']}', `database_knowledge` = '{request.form['database_knowledge']}', `networking_knowledge` = '{request.form['networking_knowledge']}' 
WHERE `student`.`email` = '{session.get('email')}' AND `student`.`nric` = '{session.get('nric')}';'''
        cursor.execute(insert_sql)
        db_conn.commit()
    except Exception as e:
        return str(e)
    finally:
        cursor.close()

    return redirect(url_for('studentHomepage', updateSuccess=True))


@app.route("/registerCompany", methods=['GET', 'POST'])
@requireStudentLogin
def registerCompany():
    
    try:
        cursor = db_conn.cursor()
        cursor.execute("select * from company WHERE deleted=0 order by name")
        companies = cursor.fetchall()
    except Exception as e:
        return str(e)
    finally:
        cursor.close()

    return render_template('registerCompany.html', companies=companies)


@app.route("/registerCompanyApi", methods=['GET', 'POST'])
@requireStudentLogin
def registerCompanyApi():

    companyId = request.form['company']
    allowance = request.form['allowance']
    sup_name = request.form['company_sup_name']
    sup_email = request.form['company_sup_email']
    acceptance_form = request.files['acceptance_form']
    ack_form = request.files['ack_form']
    indemnity_form = request.files['indemnity_form']

    # Upload files to S3 first
    acf_url = ""
    ack_url = ""
    ind_url = ""
    try:
        acf_filename_in_s3 = f"forms/{session.get('nric')}/company_acceptance_form"
        ack_filename_in_s3 = f"forms/{session.get('nric')}/parent_acknowledgement_form"
        ind_filename_in_s3 = f"forms/{session.get('nric')}/letter_of_indemnity"

        s3 = boto3.resource('s3')
        s3.Bucket(custombucket).put_object(
            Key=acf_filename_in_s3, Body=acceptance_form, ContentType=acceptance_form.content_type)
        s3.Bucket(custombucket).put_object(
            Key=ack_filename_in_s3, Body=ack_form, ContentType=ack_form.content_type)
        s3.Bucket(custombucket).put_object(
            Key=ind_filename_in_s3, Body=indemnity_form, ContentType=indemnity_form.content_type)

        bucket_location = boto3.client(
            's3').get_bucket_location(Bucket=custombucket)
        s3_location = (bucket_location['LocationConstraint'])

        if s3_location is None:
            s3_location = ''
        else:
            s3_location = '-' + s3_location

        acf_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
            s3_location,
            custombucket,
            acf_filename_in_s3)
        ack_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
            s3_location,
            custombucket,
            ack_filename_in_s3)
        ind_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
            s3_location,
            custombucket,
            ind_filename_in_s3)

    except Exception as e:
        return str(e)

    # Insert data to SQL/RDS
    try:
        cursor = db_conn.cursor()
        cursor.execute(f'''
                        SELECT `student`.`id`
                        FROM `student`
                        WHERE `student`.`nric` = '{session.get('nric')}' AND `student`.`email` = '{session.get('email')}' AND `deleted` = '0';
                       ''')
        output = cursor.fetchall()
        if len(output) == 0:
            return "Student data not found!"

        student_id = output[0][0]

        cursor.execute(
            f"INSERT INTO `student_company` (`id`, `student_id`, `company_id`, `monthly_allowance`, `company_supervisor_name`, `company_supervisor_email`, `company_acceptance_form_url`, `parent_acknowledgement_form_url`, `letter_of_indemnity_url`, `deleted`) VALUES (NULL, '{student_id}', '{companyId}', '{allowance}', '{sup_name}', '{sup_email}', '{acf_url}', '{ack_url}', '{ind_url}', '0');")
        db_conn.commit()

    except Exception as e:
        return str(e)
    finally:
        cursor.close()

    return redirect(url_for('studentHomepage'))


@app.route("/studentViewReports", methods=["GET", "POST"])
@requireStudentLogin
def studentViewReports():

    updateSuccess = request.args.get('updateSuccess')

    reports = ()
    student_id = ""
    
    try:
        cursor = db_conn.cursor()

        # Get Student ID (because it will be used later)
        cursor.execute(f'''
                        SELECT * FROM student 
                        WHERE deleted='0' AND nric='{session.get('nric')}' AND email='{session.get('email')}';
                        ''')
        output = cursor.fetchall()
        if len(output) == 0:
            return "Student data not found!"

        student_id = output[0][0]

        # Get student reports
        cursor.execute(f'''
                        SELECT * FROM student_report 
                        WHERE deleted='0' AND student_id='{student_id}';
                        ''')
        reports = cursor.fetchall()

    except Exception as e:
        return str(e)
    finally:
        cursor.close()

    reportDatetimes = []
    for each in reports:
        reportDatetimes.append(datetime.fromtimestamp(each[3]).strftime('%Y-%m-%d %H:%M:%S'))

    return render_template('studentViewReports.html', updateSuccess=updateSuccess, reports=reports, reportDatetimes=reportDatetimes)

@app.route("/studentSubmitReport", methods=["GET", "POST"])
@requireStudentLogin
def studentSubmitReport():
    return render_template('studentSubmitReport.html')

@app.route("/studentSubmitReportApi", methods=["POST"])
@requireStudentLogin
def studentSubmitReportApi():

    reportType = request.form['reportType']
    reportName = request.form['reportName']
    reportFile = request.files['reportFile']

    # Get current report number before saving to S3
    student_id = ""
    reportLength = 0
    try:
        cursor = db_conn.cursor()

        # Get Student ID (because it will be used later)
        cursor.execute(f'''
                        SELECT * FROM student
                        WHERE deleted='0' AND nric='{session.get('nric')}' AND email='{session.get('email')}';
                        ''')
        output = cursor.fetchall()
        if len(output) == 0:
            return "Student data not found!"

        student_id = output[0][0]

        # Get student reports
        cursor.execute(f'''
                        SELECT * FROM student_report
                        WHERE deleted='0' AND student_id='{student_id}';
                        ''')
        output = cursor.fetchall()
        reportLength = len(output)

    except Exception as e:
        return "Exception at getting student information: " + str(e)
    finally:
        cursor.close()

    # Upload files to S3
    report_url = ""
    try:
        report_filename_in_s3 = ""
        if (reportType == "Progress"):
            report_filename_in_s3 = f"reports/{session.get('nric')}/progressReport-{reportLength + 1}"
        else:
            report_filename_in_s3 = f"reports/{session.get('nric')}/finalReport-{reportLength + 1}"

        s3 = boto3.resource('s3')
        s3.Bucket(custombucket).put_object(
            Key=report_filename_in_s3, Body=reportFile, ContentType=reportFile.content_type)

        bucket_location = boto3.client(
            's3').get_bucket_location(Bucket=custombucket)
        s3_location = (bucket_location['LocationConstraint'])

        if s3_location is None:
            s3_location = ''
        else:
            s3_location = '-' + s3_location

        report_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
            s3_location,
            custombucket,
            report_filename_in_s3)

    except Exception as e:
        return "Exception at uploading to S3: " + str(e)

    # Insert data to SQL/RDS
    try:
        current_datetime = int(datetime.now().timestamp())

        cursor = db_conn.cursor()
        cursor.execute(
            f"INSERT INTO `student_report` (`student_id`, `type`, `submission_date`, `report_url`, `report_name`) VALUES ('{student_id}', '{reportType}', '{current_datetime}', '{report_url}', '{reportName}');")
        db_conn.commit()

    except Exception as e:
        return "Exception at inserting into SQL: " + str(e)
    finally:
        cursor.close()
    
    return redirect(url_for('studentViewReports', updateSuccess=True))


@app.route("/login", methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('studentHomepage'))

    invalidLogin = request.args.get('invalidLogin')
    notLoggedInWarning = request.args.get('notLoggedInWarning')

    return render_template('login.html', notLoggedInWarning = notLoggedInWarning, invalidLogin=invalidLogin)


@app.route("/loginApi", methods=['POST'])
def loginApi():
    email = request.form['email']
    nric = request.form['nric']

    try:
        cursor = db_conn.cursor()
        cursor.execute(f"select nric, email from student WHERE deleted=0 AND email='{email}' AND nric='{nric}'")
        output = cursor.fetchone()
    except Exception as e:
        return str(e)
    finally:
        cursor.close()

    if output != None:
        session['logged_in'] = True
        session['email'] = email
        session['nric'] = nric
        return redirect(url_for('studentHomepage'))

    return render_template('login.html', invalidLogin=True)


@app.route("/logoutApi", methods=['GET', 'POST'])
def logoutApi():
    session["logged_in"] = False
    session["email"] = ""
    session["nric"] = ""
    return redirect(url_for('home'))


# ======================================================
# ADMIN
# ======================================================

@app.route("/adminLogin", methods=['GET'])
def adminLogin():
    if session.get('admin_logged_in'):
        return redirect(url_for('adminHomepage'))
    
    notLoggedInWarning = request.args.get('notLoggedInWarning')
    invalidLogin = request.args.get('invalidLogin')
    return render_template('adminLogin.html', notLoggedInWarning=notLoggedInWarning, invalidLogin=invalidLogin)

@app.route("/adminLogin", methods=["POST"])
def adminLoginApi():
    username = request.form['username']
    password = request.form['password']

    encryptedPassword = hash_admin_password(password)

    try:
        cursor = db_conn.cursor()
        cursor.execute(f"SELECT id FROM admin WHERE deleted='0' AND username='{username}' AND password='{encryptedPassword}';")
        output = cursor.fetchone()
    except Exception as e:
        return str(e)
    finally:
        cursor.close()
    
    if (output != None):
        session['admin_logged_in'] = True
        return redirect(url_for('adminHomepage'))

    return render_template('adminLogin.html', invalidLogin=True)

@app.route("/adminLogoutApi", methods=["GET", "POST"])
def adminLogoutApi():
    session['admin_logged_in'] = False
    return redirect(url_for('home'))

@app.route("/adminHomepage", methods=["GET"])
@requireAdminLogin
def adminHomepage():
    studInfo = selectAllFromTable("student")
    programmeInfo = selectAllFromTable("programme")
    studCompany = selectAllFromTable("student_company")

    studCompanySubmitted = []
    for studRow in studInfo:
        found = False
        for compRow in studCompany:
            if compRow[0] == studRow[0]:
                found = True
                break
        if found:
            studCompanySubmitted.append("Submitted")
        else:
            studCompanySubmitted.append("Not Submitted")

    # Render an HTML template with the retrieved data
    return render_template('adminHomepage.html', invalidLogin=True, studInfo=studInfo, programmeInfo=programmeInfo, studCompanySubmitted=studCompanySubmitted)

@app.route("/adminEditPortfolio", methods=['GET', 'POST'])
@requireAdminLogin
def adminEditPortfolio():
    idParam = request.args.get('id')

    edulevelList = selectAllFromTable("education_level")
    cohortList = selectAllFromTable("cohort")
    programmeList = selectAllFromTable("programme")
    supervisorList = selectAllFromTable("supervisor")

    try:
        # Insert record to sql
        cursor = db_conn.cursor()
        cursor.execute(
            f"SELECT * FROM student WHERE id='{idParam}' AND deleted='0';")
        output = cursor.fetchall()
        if len(output) == 0:
            return "Student Information not found!"

        # Student Table Columns
        cursor.execute(
            f"select column_name from information_schema.columns where table_name = N'student' and table_schema='{customdb}' order by ordinal_position")
        studentColumns = cursor.fetchall()

    except Exception as e:
        return str(e)
    finally:
        cursor.close()

    studentInfo = {}
    for i, col in enumerate(studentColumns):
        studentInfo[col[0]] = output[0][i]

    studentInfo['education_level_name'] = [i[1]
                                           for i in edulevelList if i[0] == studentInfo['education_level_id']][0]
    studentInfo['cohort_name'], studentInfo['cohort_period'] = [
        (i[1], i[2]) for i in cohortList if i[0] == studentInfo['cohort_id']][0]
    studentInfo['programme_name'], studentInfo['programme_code'] = [
        (i[1], i[2]) for i in programmeList if i[0] == studentInfo['programme_id']][0]
    studentInfo['supervisor_name'], studentInfo['supervisor_email'] = [
        (i[1], i[2]) for i in supervisorList if i[0] == studentInfo['supervisor_id']][0]

    return render_template('adminEditPortfolio.html',
                           edulevelList=edulevelList,
                           cohortList=cohortList,
                           programmeList=programmeList,
                           programmeListJson=json.dumps(programmeList),
                           supervisorList=supervisorList,
                           studentInfo=studentInfo, idParam=idParam)


@app.route("/adminEditPortfolioApi", methods=['POST'])
@requireAdminLogin
def adminEditPortfolioApi():

    idParam = request.args.get('id')
    profile_picture = request.files['profile_picture']
    student_id = request.form['student_id']

    # If user updated profile pic
    pfp_url = ""
    if (profile_picture):
        # Upload picture to s3
        try:
            pfp_filename_in_s3 = "pfp/" + "pfp-" + str(student_id)

            s3 = boto3.resource('s3')
            s3.Bucket(custombucket).put_object(
                Key=pfp_filename_in_s3, Body=profile_picture, ContentType=profile_picture.content_type)
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

    # Update SQL
    try:
        cursor = db_conn.cursor()
        insert_sql = ""
        if (profile_picture and len(pfp_url) > 0):
            insert_sql = f'''
UPDATE `student` 
SET `profile_picture_url`='{pfp_url}', `name` = '{request.form['name']}', `gender` = '{request.form['gender']}', `transport` = '{request.form['transport']}', `health_remark` = '{request.form['health_remark']}', `student_id` = '{request.form['student_id']}', `tutorial_group` = '{request.form['tutorial_group']}', `cgpa` = '{request.form['cgpa']}', `education_level_id` = '{request.form['education_level']}', `cohort_id` = '{request.form['cohort']}', `programme_id` = '{request.form['programme']}', `supervisor_id` = '{request.form['supervisor']}', `term_address` = '{request.form['term_address']}', `permanent_address` = '{request.form['permanent_address']}', `mobile_phone` = '{request.form['mobile_phone']}', `fixed_phone` = '{request.form['fixed_phone']}', `programming_knowledge` = '{request.form['programming_knowledge']}', `database_knowledge` = '{request.form['database_knowledge']}', `networking_knowledge` = '{request.form['networking_knowledge']}' 
WHERE `student`.`id` = '{idParam}';'''
        else:
            insert_sql = f'''
UPDATE `student` 
SET `name` = '{request.form['name']}', `gender` = '{request.form['gender']}', `transport` = '{request.form['transport']}', `health_remark` = '{request.form['health_remark']}', `student_id` = '{request.form['student_id']}', `tutorial_group` = '{request.form['tutorial_group']}', `cgpa` = '{request.form['cgpa']}', `education_level_id` = '{request.form['education_level']}', `cohort_id` = '{request.form['cohort']}', `programme_id` = '{request.form['programme']}', `supervisor_id` = '{request.form['supervisor']}', `term_address` = '{request.form['term_address']}', `permanent_address` = '{request.form['permanent_address']}', `mobile_phone` = '{request.form['mobile_phone']}', `fixed_phone` = '{request.form['fixed_phone']}', `programming_knowledge` = '{request.form['programming_knowledge']}', `database_knowledge` = '{request.form['database_knowledge']}', `networking_knowledge` = '{request.form['networking_knowledge']}' 
WHERE `student`.`id` = '{idParam}';'''
        cursor.execute(insert_sql)
        db_conn.commit()
    except Exception as e:
        return str(e)
    finally:
        cursor.close()

    return redirect(url_for('adminHomepage'))

@app.route("/studentDetail", methods=["GET"])
@requireAdminLogin
def studentDetail():
    
    idParam = request.args.get('id')

    if (not idParam) or idParam == "":
        return redirect(url_for('adminHomepage'))

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
            WHERE `student`.`deleted`='0'
                AND `student`.`id` = '{idParam}' ;
            ''')
        output = cursor.fetchall()

        # Student Table Columns
        cursor.execute(
            f"select column_name from information_schema.columns where table_name = N'student' and table_schema='{customdb}' order by ordinal_position")
        columns = cursor.fetchall()

        # Company Info
        cursor.execute(f'''
            SELECT student_company.*, company.*
            FROM student_company
                LEFT JOIN company ON student_company.company_id = company.id
            WHERE student_company.student_id = '{idParam}' AND student_company.deleted = '0' AND company.deleted = '0';
            ''')
        companyOutput = cursor.fetchall()

        # Company columns
        cursor.execute(
            f"select column_name from information_schema.columns where table_name = N'student_company' and table_schema='{customdb}' order by ordinal_position")
        scColumns = cursor.fetchall()
        cursor.execute(
            f"select column_name from information_schema.columns where table_name = N'company' and table_schema='{customdb}' order by ordinal_position")
        cColumns = cursor.fetchall()

    except Exception as e:
        return str(e)
    finally:
        cursor.close()

    fColumns = list(map(lambda x: x[0], columns))
    fColumns.extend(["cohort_name", "cohort_period", "education_level_name",
                    "programme_name", "programme_code", "supervisor_name", "supervisor_email"])

    fOutput = {}
    for i, each in enumerate(fColumns):
        fOutput[each] = output[0][i]

    companyInfo = False
    if len(companyOutput) > 0:
        companyInfo = {}
        tempColumns = list(scColumns)
        tempColumns.extend(list(cColumns))
        for i, each in enumerate(tempColumns):
            companyInfo[each[0]] = companyOutput[0][i]
    
    print(fOutput)
    print(fColumns)
    print(companyInfo)

    return render_template('studentDetail.html', studInfo=fOutput, companyInfo=companyInfo)

@app.route("/adminCompanyPage", methods=["GET"])
@requireAdminLogin
def adminCompanyPage():

    invalidMsg = request.args.get('invalid')
    updateSuccess = request.args.get('updateSuccess')
    companies = selectAllFromTable("company")
    return render_template('adminCompanyPage.html', companies=companies, invalidMsg=invalidMsg, updateSuccess=updateSuccess)

@app.route("/addCompany", methods=["GET", "POST"])
@requireAdminLogin
def addCompany():

    updateSuccessParam = request.args.get('updateSuccess')
    return render_template('addCompany.html', updateSuccess=updateSuccessParam)


@app.route("/addCompanyApi", methods=["POST"])
@requireAdminLogin
def addCompanyApi():

    name = request.form['name']
    address_1 = request.form['address_1']
    address_2 = request.form['address_2']

    if address_2 == "":
        address_2 = " - "
    try:
        # Insert record to sql
        cursor = db_conn.cursor()
        insert_sql = f"INSERT INTO `company` (`name`, `address_1`, `address_2`) VALUES ('{name}', '{address_1}', '{address_2}');"
        cursor.execute(insert_sql)
        db_conn.commit()
    except Exception as e:
        return "Exception at SQL: " + str(e)
    finally:
        cursor.close()

    return redirect(url_for('addCompany', updateSuccess=True))


@app.route("/editCompany", methods=["GET", "POST"])
@requireAdminLogin
def editCompany():

    companyId = request.args.get('id')

    if (not companyId) or companyId == "":
        return redirect(url_for('adminCompanyPage', invalid='Invalid Company ID'))
    
    try:
        cursor = db_conn.cursor()
        cursor.execute(f"SELECT * FROM company WHERE deleted = 0 AND id = {companyId}")
        output = cursor.fetchall()
    except Exception as e:
        return str(e)
    finally:
        cursor.close()

    if len(output) == 0:
        return redirect(url_for('adminCompanyPage', invalid='Company data not found!'))
    
    return render_template('editCompany.html', companyInfo=output[0])


@app.route("/editCompanyApi", methods=["POST"])
@requireAdminLogin
def editCompanyApi():

    name = request.form['name']
    address_1 = request.form['address_1']
    address_2 = request.form['address_2']
    companyId = request.form['companyId']

    if address_2 == "":
        address_2 = " - "
    try:
        # Insert record to sql
        cursor = db_conn.cursor()
        sql = f"UPDATE company SET `name`='{name}', `address_1`='{address_1}', `address_2`='{address_2}' WHERE deleted=0 AND id={companyId}"
        cursor.execute(sql)
        db_conn.commit()
    except Exception as e:
        return "Exception at SQL: " + str(e)
    finally:
        cursor.close()

    return redirect(url_for('adminCompanyPage', updateSuccess=True))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)