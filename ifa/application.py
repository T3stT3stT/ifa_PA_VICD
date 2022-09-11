import os
from flask import Flask, flash, render_template, redirect, url_for, request, session, send_from_directory, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import numpy as np
from werkzeug.utils import secure_filename
import mysql.connector
import sys
import base64
import io
import PIL.Image

IMAGES_FOLDER = os.path.join('static', 'images')
ALLOWED_EXTENSIONS = {'png','jpg','jpeg'}

app = Flask(__name__, template_folder='temp')

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'test'

# Enter your database connection details below
app.config['MYSQL_HOST'] = '10.0.0.6'
app.config['MYSQL_USER'] = 'dba01'
app.config['MYSQL_PASSWORD'] = 'Pass123$$'
app.config['MYSQL_DB'] = 'pythonlogin'
app.config['UPLOAD_FOLDER'] = IMAGES_FOLDER
#connection = mysql.connector.connect(host='10.0.0.6', database='pythonlogin', user='dba01', password='Pass123$$')

mysql = MySQL(app)

#Redirects request to '/' to '/diagnose'
@app.route('/')
def index():
    return redirect(url_for('diagnose'))
#get disease with id
@app.route('/get/diseases/<id>', methods=['GET'])
def get(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM diseases WHERE dID = %s', (id,))
    diseases_id = cursor.fetchall()
    response = jsonify(diseases_id)
    return response

# http://localhost:5000/pythonlogin/ - the following will be our login page, which will use both GET and POST requests
@app.route('/login', methods=['GET', 'POST'])
def login():
 # Output message if something goes  wrong...
        msg = ''

# Check if "username" and "password" POST requests exist (user submitted form)
        if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
                        
# Create variables for easy access
            username = request.form['username']
            password = request.form['password']
# Check if account exists using MySQL
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
# Fetch one record and return result
            account = cursor.fetchone()

# If account exists in accounts table in out database
            if account:

# Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
# Redirect to home page
                return redirect(url_for('home'))
            else:
# Account doesnt exist or username/password incorrect
                return render_template('index.html', msg='Incorrect username/password!')    
        return render_template('index.html', msg='')


# http://localhost:5000/logout - this will be the logout page
@app.route('/login/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))  
 
# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/login/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        input_medNR = request.form['medNR']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        medNR = cursor.execute('SELECT * FROM medicalNRproof WHERE medical_nr = %s',(input_medNR,))
        checkmed = cursor.execute('SELECT * FROM accounts WHERE medNR = %s', (input_medNR,))
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif medNR == 0:
            msg = 'Your medical license number is invalid!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'   
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        elif checkmed:
            msg = 'Medical License Number is already reigsterd!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s, %s)', (username, password, email, input_medNR,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for loggedin users
@app.route('/login/home', methods=['GET','POST'])
def home():
    msg=''
    # Check if user is loggedin
    if 'loggedin' in session and request.method == 'POST' and 'dbsym1' in request.form and 'dbsym2' in request.form and 'dbsym3' in request.form and 'dbsym4' in request.form and 'dbsym5' in request.form:
        dname=request.form['dname']
        probability=request.form['probability']
        dbsym1=request.form['dbsym1']
        dbsym2=request.form['dbsym2']
        dbsym3=request.form['dbsym3']
        dbsym4=request.form['dbsym4']
        dbsym5=request.form['dbsym5']
        dlink=request.form['dlink']
        username=session['username']
        img1=request.files['img1']
        img=  img1.filename
        #img_filename=img.filename
        img1.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(img1.filename)))
         

        #create sym array for for loop
        symDB= np.array([dbsym1,dbsym2,dbsym3,dbsym4,dbsym5])     
        
        #Creta DB connection
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
       
        #Check if the diseases exists already
        check_dname = cursor.execute('SELECT * FROM diseases WHERE dname = %s',(dname,))
        if check_dname == 0:
            cursor.execute('INSERT INTO diseases VALUES (NULL, %s, %s, %s, %s, %s)',(dname, probability, dlink, username, img,))
            mysql.connection.commit()           
                    
            #Check if symptom exists, if not create in tables symptoms
            for i in symDB:
            
                #check symptom and write in array
                check_sym = cursor.execute('SELECT * FROM symptoms WHERE symptom = %s',(i,))         
            
                if check_sym == 0:
                    cursor.execute('INSERT INTO symptoms VALUES (NULL, %s, %s)',(i, dname,))
                    mysql.connection.commit()

                #create symptom
                elif check_sym == 1:
                    dname_wc = "%" + dname + "%"
                    check_dis = cursor.execute('SELECT * FROM symptoms WHERE symptom = %s AND dname LIKE %s',(i,dname_wc,))   
                    
                    if check_dis == 0:
                        cursor.execute('SELECT dname FROM symptoms WHERE symptom = %s',(i,))
                        sym_dis = cursor.fetchone()
                        dname_db = sym_dis['dname']
                        dname_db += ',' + dname
                        cursor.execute('UPDATE symptoms SET dname = %s  WHERE symptom = %s',(dname_db, i,))
                        mysql.connection.commit()

        # Return to home of successful
            msg="Disease was registered successfully!"
            return render_template('home.html', username=session['username'], msg=msg)
        
        else:
            msg= 'Disease is already registerd!'
            return render_template('home.html', username=session['username'], msg=msg)
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'])
    
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# http://localhost:5000/pythinlogin/profile - this will be the profile page, only accessible for loggedin users
@app.route('/login/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        #cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))

        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

#Check if medical Licensenumber is registered
@app.route('/check', methods=['GET','POST'])
def check():
    msg=''    
    
    if request.method == 'POST':
        test = request.form.get('medicalNR')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        medNR = cursor.execute('SELECT * FROM medicalNRproof WHERE medical_nr = %s',(test,))
        if medNR == 1:
            msg = 'Your medical license number IS valid!'
        else:
            msg = 'Your medical license number is NOT valid!'
    return render_template('check.html', msg=msg)

# Route for user symptom diagnose
@app.route('/diagnose', methods=['GET','POST'])
def diagnose():
    msg=''
    if 'fsym1' in request.form and 'fsym2' in request.form and 'fsym3' in request.form and 'fsym4' in request.form and 'fsym5' in request.form:

        fsym1=request.form['fsym1']
        fsym2=request.form['fsym2']
        fsym3=request.form['fsym3']
        fsym4=request.form['fsym4']
        fsym5=request.form['fsym5']
        
        symFs = np.array([fsym1,fsym2,fsym3,fsym4,fsym5])  
        dis_arr = np.array([])
        arr_discount = np.array([])
        prob_arr = np.array([])
        
        for fs in symFs:
            #connect db
            #serach diseases
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            dis_db = cursor.execute('SELECT dname FROM symptoms WHERE symptom = %s', (fs,))
            if dis_db == 0:
                pass
            
            else:
                dis_clean = cursor.fetchone()
                dis_dname = dis_clean['dname']
                dis_sep = dis_dname.split(",")
                dis_arr = np.append(dis_arr, dis_sep)
            #return f'{dis_arr}'
        #return f't {dis_arr}  s'        
        for d in dis_arr:            
            check_tempdb = cursor.execute('SELECT * FROM temp_ranking WHERE rname = %s', (d,))
            
            if check_tempdb == 0:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                dis_dbd = cursor.execute('SELECT probability FROM diseases WHERE dname = %s', (d,))
                prob_fetch = cursor.fetchone()
                prob_value = prob_fetch['probability']
                #return f't {prob_value}  s'
                arr_count = np.count_nonzero(dis_arr == d)
                #return f' s {arr_count} s ' 
                dict = {d: arr_count}
                arr_discount = np.append(arr_discount, np.array(dict))
                dis_arr = dis_arr[dis_arr != d]                    
            
                if arr_count == 0:
                    arr_count_i = 0
                if arr_count == 1:
                    arr_count_i = 20
                if arr_count == 2:
                    arr_count_i = 600
                if arr_count == 3:
                    arr_count_i = 1200
                if arr_count == 4:
                    arr_count_i = 3000
                if arr_count == 5:
                    arr_count_i = 12000
                
                #wahrscheinlichkeit ausrechnen
                prob_dis = prob_value * arr_count_i
                cursor.execute('INSERT INTO temp_ranking VALUES (NULL, %s, %s)',(d,prob_dis))
                mysql.connection.commit()  
            
            elif check_tempdb == 1:
                    pass

        return redirect(url_for('results'))

    return render_template("diagnose.html")    
    

# Route for diagnose resluts
@app.route('/results', methods=['GET'])
def results():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    db_rank = cursor.execute('select rname from temp_ranking order by rprob desc limit 0,3')
    fetch_rank = [item['rname'] for item in cursor.fetchall()]
    rname=[]
    rimg=[]
    rlink=[]
    rprob=[]
    
    img_path = os.path.join(app.config['UPLOAD_FOLDER']) 
    for r in fetch_rank:
        #search rname
        db_rname = cursor.execute('SELECT dname FROM diseases WHERE dname = %s', (r,))
        fetch_rname = cursor.fetchone()
        clean_rname = fetch_rname['dname']
        rname.append(clean_rname)
        #Get the link
        db_rlink = cursor.execute('SELECT dlink FROM diseases WHERE dname = %s', (r,))
        fetch_rlink = cursor.fetchone()
        clean_rlink = fetch_rlink['dlink']
        rlink.append(clean_rlink)
        #Get the image
        db_rimg = cursor.execute('SELECT dimg FROM diseases WHERE dname = %s', (r,))
        fetch_rimg = cursor.fetchone()
        clean_rimg = fetch_rimg['dimg']       
        rimg.append(clean_rimg)       
        #get matching score
        db_rprob= cursor.execute('SELECT rprob FROM temp_ranking WHERE rname = %s', (r,))
        fetch_rprob = cursor.fetchone()
        clean_rprob = fetch_rprob['rprob']       
        rprob.append(clean_rprob)
        
    cursor.execute('delete from temp_ranking')
    mysql.connection.commit()
    
    #create path to images
    rimg1_p = os.path.join(app.config['UPLOAD_FOLDER'], rimg[0])
    rimg2_p = os.path.join(app.config['UPLOAD_FOLDER'], rimg[1])
    rimg3_p = os.path.join(app.config['UPLOAD_FOLDER'], rimg[2])
    
    #Löschen des inhaltes der temp_table, hat jeodhc nicht geklappt
    #cursor.execute("TRUNCATE TABLE temp_ranking")
    #cursor.commit()
    #cursor.close

    #return render_template("diagnose_results.html")
    return render_template('diagnose_results.html', dimg1 = rimg1_p, dimg2 = rimg2_p, dimg3 = rimg3_p, dname1 = rname[0], dname2 = rname[1], dname3 = rname[2], dlink1 = rlink[0], dlink2 = rlink[1], dlink3 = rlink[2], dprob1 = rprob[0], dprob2 = rprob[1], dprob3 = rprob[2])

# Route um testbild anzuzeigen
#@app.route('/pic', methods=['GET'])
#def pic():
#    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#    img_dbraw = cursor.execute('SELECT dimg FROM diseases WHERE dID = 49')
#    img_db = cursor.fetchone()
#    img_name = img_db['dimg']
#       
#    img_path = os.path.join(app.config['UPLOAD_FOLDER'], img_name)
#    return render_template('results.html', image = img_path)
