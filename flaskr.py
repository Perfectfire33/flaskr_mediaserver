# all the imports
import os, time
from datetime import date
import sqlite3
import sys
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, send_from_directory
from werkzeug.utils import secure_filename
from flask_script import Manager, Server


""" ---------------- ---------------- App Init ---------------- ---------------- """
UPLOAD_FOLDER = 'c:/Users/Joseph/Downloads/Media_Server_Upload'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
DOWNLOAD_FROM_DIRECTORY = 'c:/Users/Joseph/Downloads/Media_Server_Upload'
WORK_DIRECTORY = 'c:/Users/Joseph/Documents/GitHub/flaskr_mediaserver/'
SQL_DIRECTORY = 'sql/'

# create our little application :)
app = Flask(__name__)

app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FROM_DIRECTORY'] = DOWNLOAD_FROM_DIRECTORY
# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='testing'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

# Called in
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS





""" ---------------- ---------------- Database Functions ---------------- ---------------- """
def connect_db():
    #Connects to the specific database
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    #Opens a new database connection if there is none yet for the current application context
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    #Closes the database again at the end of the request
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    #db.execute('PRAGMA FOREIGN_KEYS=ON')
    #db.execute('PRAGMA foreign_keys  = "1"')
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    #Initializes the database
    init_db()
    print('Initialized the database.')





""" ---------------- ---------------- General Functions ---------------- ---------------- """
#Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            
            #return redirect(url_for('item_list'))
            return render_template('dashboard.html')
    return render_template('login.html', error=error)

#Logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    #return redirect(url_for('item_list'))
    return render_template('dashboard.html')

    
#Get row count of a table
def get_next_row(currentTable):
    sql_string = open('sql/select_row_count.sql', 'r').read()
    sql_string = sql_string.replace("currentTable", currentTable)
    db = get_db()
    cur = db.execute(sql_string)
    row_count = cur.fetchone()
    return row_count
    
""" ---------------- ---------------- Main Routes ---------------- ---------------- """
#Display Data - Dashboard
@app.route('/')
def dashboard():
    return render_template('dashboard.html')



#Show the settings page
# Need to add in DB: a table and place to put the settings like file server save location
@app.route('/mediaserver_settings', methods=['GET', 'POST'])
def mediaserver_settings():
    db = get_db()
    sql_string = open(WORK_DIRECTORY + SQL_DIRECTORY + 'select_settings.sql', 'r').read()
    cur = db.execute(sql_string)
    default_upload_path = cur.fetchall()
    print("default_upload_path")
    print(default_upload_path[0])
    print("default_upload_path")
    return render_template('mediaserver_settings.html', default_upload_path=default_upload_path)


@app.route('/save_settings', methods=['POST'])
def mediaserver_save_settings():
    # add db stuff here to add the save location to db
    # or can use a text file to store the data
    # then need to retrieve the save location foZr use
    db = get_db()
    sql_string = open(WORK_DIRECTORY + SQL_DIRECTORY + 'delete_settings.sql', 'r').read()
    db.execute(sql_string)
    db.commit()
    sql_string = open(WORK_DIRECTORY + SQL_DIRECTORY + 'insert_settings.sql', 'r').read()
    db.execute(sql_string, [request.form['server_file_path']])
    db.commit()
    app.config['UPLOAD_FOLDER'] = request.form['server_file_path']
    app.config['DOWNLOAD_FROM_DIRECTORY'] = request.form['server_file_path']


    return redirect(url_for('mediaserver_settings'))



"""
Use DB to store filenames and folders
get filenames and folders using DB select when displaying webpage
"""

#Select all files and display webpage
@app.route('/mediaserver_list')
def mediaserver_file_list():
        # sql_string = open('sql/select_all_pcparts.sql', 'r').read()
        sql_string = open(WORK_DIRECTORY + SQL_DIRECTORY + 'select_mediaserver_file_list.sql', 'r').read()
        #Need to insert into sql folder hiearchy of file (add column to db: file_path


        db = get_db()
        cur = db.execute(sql_string)
        items = cur.fetchall()

        #Get array of files and folders in the download directory
        files_and_folders = os.listdir(app.config['DOWNLOAD_FROM_DIRECTORY'])
        print("AAAAAAA")
        print(files_and_folders)
        print("AAAAAAA")
        print("AAAAAAA")
        print(files_and_folders)
        print("AAAAAAA")



        #Will use this for later (will have to build path_of_file from SQL select statement)
        #Only if we need creation time (c) or modified time (m) from the OS when file is being downloaded
        #Create array to store date.time of files in download directory
        files_creation_time = []

        for file in files_and_folders:
            path_of_file = app.config['DOWNLOAD_FROM_DIRECTORY'] + "/" + file
            print("last modified: %s" % time.ctime(os.path.getctime(path_of_file)))
            files_creation_time.append(time.ctime(os.path.getctime(path_of_file)))
            #print("created: %s" % time.ctime(os.path.getctime(file)))

        #return render_template('mediaserver_file_list.html', files_and_folders=files_and_folders)
        return render_template('mediaserver_file_list.html', items=items)


        
#@app.route('/get-files/<path:path>',methods = ['GET','POST'])
#def get_files(path):
#
#    """Download a file."""
#    try:
#        return send_from_directory(DOWNLOAD_DIRECTORY, path, as_attachment=True)
#    except FileNotFoundError:
#        abort(404)

@app.route('/mediaserver_download_file', methods=['POST'])
def mediaserver_download_file():

        # Select from DB the file (find filename, return row)
        sql_string = open(WORK_DIRECTORY + SQL_DIRECTORY + 'select_fileToDownload.sql', 'r').read()
        db = get_db()
        #abc = db.execute('PRAGMA FOREIGN_KEYS=ON')
        file = db.execute(sql_string,[request.form['file_to_download']])
        #db.commit()
        DownloadFileList = file.fetchall()
        #print("AAAAAAA 5555555   AAAAA")
        #print(DownloadFileList[0][2])
        #a11 = str(DownloadFileList[0][2])
        #print(a11)
        #a12 = a11.split('.')
        #print(a12)
        abc = DownloadFileList[0][2].split('\\')
        file_path = abc[0]
        #print("file_path")
        #print(file_path)
        #print("AAAAAAA 5555555   AAAAA")

        # file_path - filepath of the file to download
        # DownloadFileList - file name of the file to download
        try:
            return send_from_directory(file_path, DownloadFileList[0][1], as_attachment=True)
        except FileNotFoundError:
            abort(404)

        flash('File downloaded from OS disk!')
        return redirect(url_for('mediaserver_file_list'))


""" ---------------- ---------------- Delete Part ---------------- ----------------"""
@app.route('/mediaserver_delete_file', methods=['POST'])
def mediaserver_delete_file():

        # Need OS operations to locate the file to delete it instead of SQL
        # save the file to the OS' hard drive
        # file.delete(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        sql_string = open(WORK_DIRECTORY + SQL_DIRECTORY + 'select_fileToDelete.sql', 'r').read()
        db = get_db()
        filepath_of_file_to_delete = db.execute(sql_string,[request.form['file_to_delete']])
        #print(filepath_of_file_to_delete)
        db_files = filepath_of_file_to_delete.fetchall()
        #print("db_files.file_id")
        #print(db_files[0][0])
        #print("db_files.file_id")
        os.remove(db_files[0][0])

        sql_string = open(WORK_DIRECTORY + SQL_DIRECTORY + 'delete_file.sql', 'r').read()

        #abc = db.execute('PRAGMA FOREIGN_KEYS=ON')
        db.execute(sql_string,[request.form['file_to_delete']])
        db.commit()
        flash('File data deleted from database and file deleted from Operating System!')
        return redirect(url_for('mediaserver_file_list'))


# save the file to the OS' hard drive
#file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))


#Display Data - a part's details
#@app.route('/pcparts_list/<int:pcPartId>/<pcPartType>/part_details/')
#def part_details(pcPartId, pcPartType):
#        selected_row = get_part_details(pcPartId, pcPartType)
        #Display the page
        #   pcPartId ==> current part id
        #   selected_row ==> the part's details
#        return render_template('/pcparts/select_ssd.html', pcPartId=pcPartId, selected_row=selected_row, pcPartType=pcPartType)




# Display Form - Add a New File
@app.route('/mediaserver_addFile.html', methods=['GET', 'POST'])
def mediaserver_addFiles():
    #pcBuildList = get_pcBuildList()

    return render_template('mediaserver_addFile.html')



# Submit POST - Add a New File
# This is the executive command (not browsable web page)
@app.route('/mediaserver_addFile', methods=['GET', 'POST'])
def add_file():
    if not session.get('logged_in'):
        abort(401)



    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        #if file and allowed_file(file.filename):
        if file:


            filename = secure_filename(file.filename)

            # insert file path here (also includes file name)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            #filepath = app.config['UPLOAD_FOLDER'] + '/'



            # save the file to the OS' hard drive
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            #Get filesize (in bytes)
            filesize = os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Need to add file and file info to sqlite database
            db = get_db()
            #sql_string = open('c:/Users/Joseph/Documents/GitHub/flaskr_mediaserver/sql/upload_file.sql', 'r').read()
            sql_string = open(WORK_DIRECTORY + SQL_DIRECTORY + 'upload_file.sql', 'r').read()
            db.execute(sql_string, [filename,
                                    filepath,
                                    filesize,
                                    date.today()
                                ])
            db.commit()
            return redirect(url_for('add_file', name=filename))

        else:
            flash('File extension not supported!')

    return render_template('mediaserver_addFile.html')

#Submit POST - Add a New File
#@app.route('/mediaserver_addFile', methods=['GET', 'POST'])
#def add_file():
#    if not session.get('logged_in'):
#        abort(401)
#
#    db = get_db()
#    sql_string = open('c:/Users/Joseph/Documents/GitHub/flaskr_mediaserver/sql/upload_file.sql', 'r').read()
#    db.execute(sql_string, [request.form['file_name'],
#                            request.form['file_data']
#                            ])
#    db.commit()
#
    #return redirect(url_for('dashboard'))
    #return render_template('dashboard.html')
#    return render_template('mediaserver_addFile.html')




