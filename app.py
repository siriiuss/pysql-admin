import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect



app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Flash mesajları için gerekli gizli anahtar
app.config['UPLOAD_FOLDER'] = 'uploads'  # Yüklenen dosyaların kaydedileceği klasör
csrf = CSRFProtect(app)
# SQLite veritabanı dosyası
DB_NAME = "todo_list.db"

def allowed_file(filename):
    # Yüklenen dosyanın geçerli uzantılara sahip olup olmadığını kontrol eder
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'db'}

@app.route('/', methods=['GET', 'POST'])
@csrf.exempt
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Dosya seçilmedi!', 'error')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('Dosya seçilmedi!', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('show_tables', filename=filename))

    return render_template('index.html')

@app.route('/show_tables/<filename>', methods=['GET', 'POST'])
@csrf.exempt
def show_tables(filename):
    conn = sqlite3.connect(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    conn.close()

    if request.method == 'POST':
        selected_table = request.form.get('table')
        if selected_table:
            return redirect(url_for('show_table_contents', filename=filename, table_name=selected_table))
        else:
            flash('Tablo seçilmedi!', 'error')
            return redirect(request.url)

    return render_template('show_tables.html', filename=filename, tables=tables)

@app.route('/show_table_contents/<filename>/<table_name>', methods=['GET', 'POST'])
@csrf.exempt
def show_table_contents(filename, table_name):
    conn = sqlite3.connect(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    table_contents = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    conn.close()

    if request.method == 'POST':
        new_task = request.form.get('new_task')
        if new_task:
            conn = sqlite3.connect(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO {table_name} (task) VALUES (?)", (new_task,))
            conn.commit()
            conn.close()
            flash('Yeni görev eklendi!', 'success')
            return redirect(request.url)

    return render_template('show_table_contents.html', filename=filename, table_name=table_name, table_contents=table_contents, column_names=column_names)

@app.route('/edit/<filename>/<table_name>/<int:task_id>', methods=['POST'])
@csrf.exempt
def edit_task(filename, table_name, task_id):
    edited_task = request.form.get('edited_task')
    if edited_task:
        conn = sqlite3.connect(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        cursor = conn.cursor()
        cursor.execute(f"UPDATE {table_name} SET task = ? WHERE id = ?", (edited_task, task_id))
        conn.commit()
        conn.close()
    return redirect(url_for('show_table_contents', filename=filename, table_name=table_name))


@app.route('/delete/<filename>/<table_name>/<int:task_id>')
@csrf.exempt
def delete_task(filename, table_name, task_id):
    conn = sqlite3.connect(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('show_table_contents', filename=filename, table_name=table_name))




if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)