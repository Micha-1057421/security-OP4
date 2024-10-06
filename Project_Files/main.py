from flask import Flask, render_template, redirect, url_for, request, session, Response, send_file
from functools import wraps
import DB
import sys
sys.path.append('..')
from flask_caching import Cache
from lib.testgpt.testgpt import TestGPT

apikey = 'API KEY HERE'

import csv
from io import StringIO


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'



cache = Cache(app)
notes = DB.notities()
categories = DB.get_categories()
teachers = DB.get_teacher()
gebruikers = DB.adminscherm()

def paginering(page, per_page, notes):
    start = (page-1)*per_page
    end = start +per_page
    return notes[start:end]

#VRAGEN GENEREREN 
def open_gen(note):
    API_key = apikey
    test_gpt = TestGPT(API_key)
    open_question = test_gpt.generate_open_question(note)
    return open_question
    
def multiple_gen(note):
    API_key = apikey
    test_gpt = TestGPT(API_key)
    mc_question = test_gpt.generate_multiple_choice_question(note)
    return mc_question

#homescreen
@app.before_request
def check_inlog():
    open_routes = ['home', 'static', 'login']
    user = session.get('user')
    
    if not user and request.endpoint not in open_routes:
        return redirect(url_for('login'))
@app.route("/")
@app.route("/home")
def home():
    return render_template('homepage.html')

#login screen
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['teacher_password']

        user = DB.Login(username, password)
        if user:
            session["user"] = user
            print(user)
            return redirect(url_for("display_notes"))
        else:
            error = 'Invalid username or password. Please try again.'
            return render_template('login_page.html', error=error)
    return render_template('login_page.html')

#logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

#delete note
@app.route('/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    if request.method == 'POST':
        if DB.delete(note_id):
            return redirect(url_for('display_notes'))
        else:
            return 'Notities verwijderen mislukt'
    else:
        return redirect(url_for('display_notes'))



#view notes
@app.route("/overzicht", methods=['GET', 'POST'])
@cache.cached(timeout=60)
def display_notes():
    notes = DB.notities()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    total_notes = len(notes)
    paginated_notes = paginering(page, per_page, notes)
    aantal_notities = DB.aantalnotities()
    if not paginated_notes and page != 1:
        return "page not found", 404

    categories_list = list(DB.get_categories())
    return render_template('overzicht_notities.html', page=page, notes=paginated_notes, total_notes=total_notes,
                           per_page=per_page, aantal_notities=aantal_notities, categories_list=categories_list)

@app.route("/search", methods=['POST'])
def search_notes():
    zoekterm = request.form.get('zoekterm', '')
    zoekresultaten = DB.zoek_notities(zoekterm)
    return render_template('overzicht_notities.html', notes=zoekresultaten, zoekterm=zoekterm, page=1, total_notes=len(zoekresultaten), per_page=4, aantal_notities=len(zoekresultaten))

@app.route("/filter_notes", methods=['POST'])
def filter_notes():
    category_omschrijving = request.form.get('category')
    user_filter = request.form.get('user_filter')

    if user_filter == 'current_user':
        user_id = session.get('user')
        filtered_notes = DB.filter_notities_op_gebruiker(user_id, own_notes=True)
    else:
        filtered_notes = DB.filter_notities_op_categorie(
            category_omschrijving) if category_omschrijving else DB.notities()

    categories_list = list(DB.get_categories())
    return render_template('overzicht_notities.html', notes=filtered_notes, page=1, total_notes=len(filtered_notes),
                           per_page=4, aantal_notities=len(filtered_notes), categories_list=categories_list)

#create notes
@app.route('/create/', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        note = request.form['note']
        note_source = request.form['note_source']
        teacher_id = session.get('user')
        category_id = request.form['categorie']


        if DB.create(title, note, note_source, teacher_id,category_id):
            return redirect(url_for('display_notes'))
    categories = DB.get_categories()
    notes = DB.notities()
    teachers = DB.get_teacher()
    return render_template('maaknotitie.html', notes=notes, categories=categories, teachers=teachers)

#edit notes
@app.route('/edit/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    note = DB.get_note_id(note_id)

    if request.method == 'POST':
        updated_title = request.form['title']
        updated_note = request.form['note']
        updated_note_source = request.form['note_source']
        updated_category_id = request.form['categorie']

        DB.update_note(note_id, updated_title, updated_note, updated_note_source, updated_category_id)
        return redirect(url_for('display_notes'))

    categories = DB.get_categories()
    teachers = DB.get_teacher()
    return render_template('edit_note.html', note=note, categories=categories, teachers=teachers)

@app.route('/delete_user/<int:teacher_id>', methods=['POST'])
def delete_teacher(teacher_id):
    if request.method == 'POST':
        if DB.delete_gebruiker(teacher_id):
            return redirect(url_for('adminmenu'))
        else:
            return 'Gebruiker verwijderen mislukt'
    else:
        return redirect(url_for('adminpage'))

@app.route('/adminpage/', methods=('GET','POST'))
def adminmenu():
    teacher_id = session.get('user')
    if DB.check_admin(teacher_id) == False:
        return redirect(url_for('display_notes'))
    if request.method == 'POST':
        username = request.form['username']
        teacher_password = request.form['teacher_password']
        display_name = request.form['display_name']
        DB.adminmenu(username, teacher_password, display_name)
    gebruikers = DB.adminscherm()
    return render_template('adminpage.html', gebruikers=gebruikers)

@app.route('/<int:teacher_id>/edit_gebruiker', methods=('GET', 'POST'))
def edit_gebruiker(teacher_id):
    teacher = DB.get_teacher_id(teacher_id)

    if request.method == 'POST':
        username = request.form['username']
        teacher_password = request.form['teacher_password']
        display_name = request.form['display_name']

        conn = DB.databaseinladen()
        conn.execute('UPDATE teachers SET username = ?, display_name = ?, teacher_password = ?'
                        'WHERE teacher_id = ?',
                         (username, display_name, teacher_password, teacher_id))
        conn.commit()
        conn.close()
        return redirect(url_for('adminmenu'))
    return render_template('bewerk_gebruiker.html',  teacher=teacher)

@app.route('/categories/', methods=('GET','POST'))
def categories():
    if request.method == 'POST':
        omschrijving = request.form['omschrijving']
        DB.categoriesaanmaken(omschrijving)
    return showcategories()

@app.route('/categoriestonen/', methods=('GET', 'POST'))
def showcategories():
    categories_list = DB.categories()
    return render_template('categories.html', categories_list=categories_list)

@app.route('/verwijder_categorie/<int:category_id>', methods=['POST'])
def verwijder_categorie_main(category_id):
    if request.method == 'POST':
        if DB.verwijder_categorie(category_id):
            return redirect(url_for('categories'))
        else:
            return 'Categorie verwijderen mislukt'
    else:
        return redirect(url_for('categories'))

@app.route('/bewerk_categorie_pagina/<int:category_id>')
def bewerk_categorie_pagina(category_id):
    category = DB.get_category_by_id(category_id)
    return render_template('bewerk_categorie.html', category=category)

@app.route('/bewerk_categorie/<int:category_id>', methods=['POST'])
def bewerk_categorie(category_id):
    if request.method == 'POST':
        new_omschrijving = request.form.get('new_omschrijving')
        DB.update_category(category_id, new_omschrijving)

    return redirect(url_for('showcategories'))
def get_note_id(note_id):
    note= DB.get_note_id(note_id)
    if note and len(note) >= 7:
        return {
    'title': note[2],
    'note': note[1],
    'note_source': note[3],
    'teacher_id': note[4],
    'category_id': note[6],
    'date_created': note[5],}
    else:
        return None


@app.route('/download_notitie/<int:note_id>')
def download_notitie(note_id):
    note = get_note_id(note_id)
    if note:
        output = StringIO()
        csv_writer = csv.writer(output)
        csv_writer.writerow(['Titel', 'Inhoud', 'Bron ', 'Leraar', 'Categorie', 'Aangemaakt op:'])
        csv_writer.writerow([note['title'], note['note'], note['note_source'], note['teacher_id'], note['category_id'], note['date_created']])
        output.seek(0)
        return Response(output, mimetype='text/csv', headers={'Content-Disposition': f'attachment;filename={note["note_id"]}.csv'})
    else:
        return 'Notitie kan niet gevonden worden', 404


@app.route('/download_alle_notities')
def download_alle_notities():
    notes= DB.notities()
    if notes:
        output = StringIO()
        csv_writer = csv.writer(output)
        csv_writer.writerow(['Titel', 'Inhoud', 'Bron', 'Leraar', 'Categorie', 'Aangemaakt op:'])
        for note in notes:
            csv_writer.writerow([note[2], note[1], note[3], note[4], note[6], note[5]])
        output.seek(0)
        return Response(output, mimetype='text/csv',headers={'Content-Disposition': f'attachment;filename=alle_notities.csv'})
    else:
        return 'Notities kunnen niet gevonden worden', 404


@app.route('/see_note/<int:note_id>' , methods=['GET'])
def see_note(note_id):
    note = DB.note(note_id)
    print("Note:", note)
    print("Note Length:", len(note))

    return render_template('see_note.html', note=note)

@app.route('/generate_question/<int:note_id>' , methods=['POST'])
def generate_question(note_id):
    note = DB.note(note_id)
    question_type = request.form.get('questionType')
    open_question = None  
    multiple_choice_question = None

    if question_type == 'open':
        open_question = open_gen(note['note'])
        DB.save_question(note_id, open_question)
    
    elif question_type == 'multiple_choice':
        multiple_choice_question = multiple_gen(note['note'])
        DB.save_question(note_id, multiple_choice_question)
    return render_template('see_note.html', note=note, open_question=open_question, multiple_choice_question=multiple_choice_question)



if __name__ == "__main__":
    app.debug = True
    app.run()
