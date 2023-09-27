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
# loginState = False
# loginNric = ""
# loginEmail = ""
loginState = True
loginNric = "021005-14-1279"
loginEmail = "thongsx-wm20@student.tarc.edu.my"

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
    pfp_url = ""
    try:
        pfp_filename_in_s3 = "pfp/" + "pfp-" + str(student_id)

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


@app.route("/studentHomepage", methods=['GET', 'POST'])
def studentHomepage():
    global loginState, loginNric, loginEmail

    if not loginState:
        return redirect(url_for('home'))

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
            WHERE `student`.`deleted`='0';
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

    return render_template('studentHomepage.html', loginInfo=(loginState, loginNric, loginEmail), studInfo=fOutput, columns=fColumns, companyInfo=companyInfo, updateSuccess=updateSuccessParam)


@app.route("/editPortfolio", methods=['GET', 'POST'])
def editPortfolio():
    global loginState, loginNric, loginEmail

    if not loginState:
        return redirect(url_for('home'))

    edulevelList = selectAllFromTable("education_level")
    cohortList = selectAllFromTable("cohort")
    programmeList = selectAllFromTable("programme")
    supervisorList = selectAllFromTable("supervisor")

    try:
        # Insert record to sql
        cursor = db_conn.cursor()
        cursor.execute(
            f"SELECT * FROM student WHERE nric='{loginNric}' AND email='{loginEmail}' AND deleted='0';")
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
def editPortfolioApi():
    if not loginState:
        return redirect(url_for('home'))

    # Personal Data
    profile_picture = request.form['profile_picture']
    name = request.form['name']
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
    term_address = request.form['term_address']
    permanent_address = request.form['permanent_address']
    mobile_phone = request.form['mobile_phone']
    fixed_phone = request.form['fixed_phone']

    # Technical Knowledge
    programming_knowledge = request.form['programming_knowledge']
    database_knowledge = request.form['database_knowledge']
    networking_knowledge = request.form['networking_knowledge']

    # If user updated profile pic
    pfp_url = ""
    if (profile_picture):
        # Upload picture to s3
        try:
            pfp_filename_in_s3 = "pfp/" + "pfp-" + str(student_id)

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

    # Update SQL
    try:
        cursor = db_conn.cursor()
        insert_sql = ""
        if (profile_picture and len(pfp_url) > 0):
            insert_sql = f'''
UPDATE `student` 
SET `profile_picture_url`='{pfp_url}', `name` = '{request.form['name']}', `gender` = '{request.form['gender']}', `transport` = '{request.form['transport']}', `health_remark` = '{request.form['health_remark']}', `student_id` = '{request.form['student_id']}', `tutorial_group` = '{request.form['tutorial_group']}', `cgpa` = '{request.form['cgpa']}', `education_level_id` = '{request.form['education_level']}', `cohort_id` = '{request.form['cohort']}', `programme_id` = '{request.form['programme']}', `supervisor_id` = '{request.form['supervisor']}', `term_address` = '{request.form['term_address']}', `permanent_address` = '{request.form['permanent_address']}', `mobile_phone` = '{request.form['mobile_phone']}', `fixed_phone` = '{request.form['fixed_phone']}', `programming_knowledge` = '{request.form['programming_knowledge']}', `database_knowledge` = '{request.form['database_knowledge']}', `networking_knowledge` = '{request.form['networking_knowledge']}' 
WHERE `student`.`email` = '{loginEmail}' AND `student`.`nric` = '{loginNric}';'''
        else:
            insert_sql = f'''
UPDATE `student` 
SET `name` = '{request.form['name']}', `gender` = '{request.form['gender']}', `transport` = '{request.form['transport']}', `health_remark` = '{request.form['health_remark']}', `student_id` = '{request.form['student_id']}', `tutorial_group` = '{request.form['tutorial_group']}', `cgpa` = '{request.form['cgpa']}', `education_level_id` = '{request.form['education_level']}', `cohort_id` = '{request.form['cohort']}', `programme_id` = '{request.form['programme']}', `supervisor_id` = '{request.form['supervisor']}', `term_address` = '{request.form['term_address']}', `permanent_address` = '{request.form['permanent_address']}', `mobile_phone` = '{request.form['mobile_phone']}', `fixed_phone` = '{request.form['fixed_phone']}', `programming_knowledge` = '{request.form['programming_knowledge']}', `database_knowledge` = '{request.form['database_knowledge']}', `networking_knowledge` = '{request.form['networking_knowledge']}' 
WHERE `student`.`email` = '{loginEmail}' AND `student`.`nric` = '{loginNric}';'''
        cursor.execute(insert_sql)
        db_conn.commit()
    except Exception as e:
        return str(e)
    finally:
        cursor.close()

    return redirect(url_for('studentHomepage', updateSuccess=True))


@app.route("/registerCompany", methods=['GET', 'POST'])
def registerCompany():
    global loginState, loginNric, loginEmail

    if not loginState:
        return redirect(url_for('home'))

    return render_template('registerCompany.html')


@app.route("/registerCompanyApi", methods=['GET', 'POST'])
def registerCompanyApi():
    global loginState, loginNric, loginEmail

    if not loginState:
        return redirect(url_for('home'))

    name = request.form['company_name']
    address_1 = request.form['company_address_1']
    address_2 = request.form['company_address_2']
    allowance = request.form['allowance']
    sup_name = request.form['company_sup_name']
    sup_email = request.form['company_sup_email']
    acceptance_form = request.form['acceptance_form']
    ack_form = request.form['ack_form']
    indemnity_form = request.form['indemnity_form']

    # Upload files to S3 first
    acf_url = ""
    ack_url = ""
    ind_url = ""
    try:
        acf_filename_in_s3 = f"forms/{loginNric}/company_acceptance_form"
        ack_filename_in_s3 = f"forms/{loginNric}/parent_acknowledgement_form"
        ind_filename_in_s3 = f"forms/{loginNric}/letter_of_indemnity"

        s3 = boto3.resource('s3')
        s3.Bucket(custombucket).put_object(
            Key=acf_filename_in_s3, Body=acceptance_form)
        s3.Bucket(custombucket).put_object(
            Key=ack_filename_in_s3, Body=ack_form)
        s3.Bucket(custombucket).put_object(
            Key=ind_filename_in_s3, Body=indemnity_form)

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
        cursor.execute(
            f"INSERT INTO `company` (`id`, `name`, `address_1`, `address_2`, `deleted`) VALUES (NULL, '{name}', '{address_1}', '{address_2}', '0');")
        db_conn.commit()

        cursor.execute(f'''
                        SELECT `student`.`id`
                        FROM `student`
                        WHERE `student`.`nric` = '{loginNric}' AND `student`.`email` = '{loginEmail}';
                       ''')
        output = cursor.fetchall()
        if len(output) == 0:
            return "Invalid login!"

        student_id = output[0][0]

        cursor.execute(f'''
                        SELECT `company`.`id`
                        FROM `company`
                        WHERE `company`.`name` = '{name}' AND `company`.`address_1` = '{address_1}' AND `company`.`address_2` = '{address_2}';
                       ''')
        output = cursor.fetchall()
        if len(output) == 0:
            return "Invalid login!"

        company_id = output[-1][0]

        cursor.execute(
            f"INSERT INTO `student_company` (`id`, `student_id`, `company_id`, `monthly_allowance`, `company_supervisor_name`, `company_supervisor_email`, `company_acceptance_form_url`, `parent_acknowledgement_form_url`, `letter_of_indemnity_url`, `deleted`) VALUES (NULL, '{student_id}', '{company_id}', '{allowance}', '{sup_name}', '{sup_email}', '{acf_url}', '{ack_url}', '{ind_url}', '0');")
        db_conn.commit()

    except Exception as e:
        return str(e)
    finally:
        cursor.close()

    return redirect(url_for('studentHomepage'))


@app.route("/test", methods=["GET"])
def test():
    cursor = db_conn.cursor()
    cursor.execute("select * from supervisor")
    output = cursor.fetchall()
    cursor.close()

    print(output)
    print(type(output))
    return render_template('test.html', output=output)


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

# ======================================================
# COMPANY
# ======================================================

@app.route("/companySignUp", methods=['GET', 'POST'])
def companySignUp():
    return render_template('companySignUp.html')

@app.route("/companyLogin", methods=['GET', 'POST'])
def companyLogin():
    return render_template('companyLogin.html')

# ======================================================
# ADMIN
# ======================================================

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
            return redirect(url_for('adminHomepage'))

    return render_template('adminLogin.html', invalidLogin=True)

@app.route("/adminLogoutApi", methods=["GET", "POST"])
def adminLogoutApi():
    global adminLoginState
    adminLoginState = False
    return redirect(url_for('home'))

@app.route("/adminHomepage", methods=["GET"])
def adminHomepage():
    return render_template('adminHomepage.html', invalidLogin=True)

@app.route("/studentDetail", methods=["GET"])
def studentDetail():
    return render_template('studentDetail.html', invalidLogin=True)

if __name__ == '__main__':
    app.run(debug=True)
