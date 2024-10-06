import sqlite3
from flask import abort

def databaseinladen():
    conn = sqlite3.connect('../databases/testgpt.db')
    return conn

def delete(note_id):
    delete_query = 'DELETE FROM notes WHERE note_id = ?'
    conn = databaseinladen()
    conn.execute(delete_query, (note_id, ))
    conn.commit()
    return True


def Login(username, password):
    query = 'SELECT username, teacher_password, teacher_id FROM teachers WHERE username=? AND teacher_password=?;'
    conn = databaseinladen()
    cursor = conn.execute(query, (username, password))
    user = cursor.fetchone()
    if user is None:
        return False
    return user[2]

def check_admin(teacher_id):
    print(teacher_id)
    query = 'SELECT teacher_id, is_admin FROM teachers WHERE teacher_id=? AND is_admin=1'
    conn = databaseinladen()
    cursor = conn.execute(query, (str(teacher_id),))
    user = cursor.fetchone()
    return user is not None

def create(title, note, note_source, teacher_id,category_id):
    notitie = 'INSERT INTO notes (title, note, note_source, teacher_id, category_id) VALUES (?,?,?,?,?)'
    conn = databaseinladen()
    curs = conn.execute(notitie, (title, note, note_source, teacher_id,category_id))
    note = curs.fetchall()
    conn.commit()
    return note is not None

def notities():
    query2 = 'SELECT notes.note_id, notes.note, notes.title, notes.note_source, teachers.display_name, notes.date_created, categories.omschrijving  FROM notes INNER JOIN categories ON notes.category_id = categories.category_id INNER JOIN teachers on teachers.teacher_id = notes.teacher_id;'
    conn = databaseinladen()
    notes = conn.execute(query2).fetchall()
    return notes

def zoek_notities(zoekterm):
    query12 = 'SELECT notes.note_id, notes.note, notes.title, notes.note_source, teachers.display_name, notes.date_created, categories.omschrijving  FROM notes INNER JOIN categories ON notes.category_id = categories.category_id INNER JOIN teachers ON teachers.teacher_id = notes.teacher_id WHERE notes.note LIKE ? OR notes.title LIKE ?;'
    conn = databaseinladen()
    resultaat = conn.execute(query12, ('%' + zoekterm + '%', '%' + zoekterm + '%')).fetchall()
    return resultaat

def filter_notities_op_categorie(categorie):
    query = 'SELECT notes.note_id, notes.note, notes.title, notes.note_source, teachers.display_name, notes.date_created, categories.omschrijving FROM notes INNER JOIN categories ON notes.category_id = categories.category_id INNER JOIN teachers ON teachers.teacher_id = notes.teacher_id WHERE categories.omschrijving = ?;'
    conn = databaseinladen()
    resultaat = conn.execute(query, (categorie,)).fetchall()
    return resultaat

def filter_notities_op_gebruiker(teacher_id, own_notes=True):
    if own_notes:
        query = 'SELECT notes.note_id, notes.note, notes.title, notes.note_source, teachers.display_name, notes.date_created, categories.omschrijving FROM notes INNER JOIN categories ON notes.category_id = categories.category_id INNER JOIN teachers ON teachers.teacher_id = notes.teacher_id WHERE teachers.teacher_id = ?;'
    else:
        query = 'SELECT notes.note_id, notes.note, notes.title, notes.note_source, teachers.display_name, notes.date_created, categories.omschrijving FROM notes INNER JOIN categories ON notes.category_id = categories.category_id INNER JOIN teachers ON teachers.teacher_id = notes.teacher_id WHERE teachers.teacher_id != ?;'

    conn = databaseinladen()
    resultaat = conn.execute(query, (teacher_id,)).fetchall()
    return resultaat
def get_categories():
    query = 'SELECT category_id, omschrijving FROM categories;'
    conn = databaseinladen()
    categories = conn.execute(query).fetchall()
    return categories

def get_teacher():
    query = 'SELECT teacher_id, display_name FROM teachers;'
    conn = databaseinladen()
    teachers = conn.execute(query).fetchone()
    return teachers

def adminmenu(username, teacher_password, display_name):
    query3 = 'INSERT INTO teachers (username, teacher_password, display_name) VALUES (?,?,?)'
    conn = databaseinladen()
    conn.execute(query3, (username, teacher_password, display_name))
    conn.commit()

def adminscherm():
    query = 'SELECT display_name, username, teacher_password, teacher_id FROM teachers;'
    conn = databaseinladen()
    gebruikers = conn.execute(query).fetchall()
    return gebruikers

def delete_gebruiker(teacher_id):
    query = 'DELETE FROM teachers WHERE teacher_id = ?'
    conn = databaseinladen()
    conn.execute(query, (teacher_id, ))
    conn.commit()
    return True


def get_teacher_id(teacher_id):
    conn = databaseinladen()
    gebruiker = conn.execute('SELECT teacher_id, display_name, username, teacher_password FROM teachers '
                             'WHERE teacher_id=?',(teacher_id,)).fetchone()
    conn.close()
    if gebruiker is None:
        abort(404)
    return gebruiker


def categoriesaanmaken(omschrijving):
    query4 = 'INSERT INTO categories (omschrijving) VALUES (?)'
    conn = databaseinladen()
    conn.execute(query4, (omschrijving,))
    conn.commit()

def categories():
    query10 = 'SELECT category_id, omschrijving, date_created FROM categories;'
    conn = databaseinladen()
    conn.row_factory = sqlite3.Row
    categories = conn.execute(query10).fetchall()
    return categories

def verwijder_categorie(category_id):
    query11 = 'DELETE FROM categories WHERE category_id = ?'
    conn = databaseinladen()
    conn.execute(query11, (category_id, ))
    conn.commit()
    return True

def get_category_by_id(category_id):
    query = 'SELECT category_id, omschrijving, date_created FROM categories WHERE category_id = ?;'

    with databaseinladen() as conn:
        conn.row_factory = sqlite3.Row
        category = conn.execute(query, (category_id,)).fetchone()

    return category

def update_category(category_id, new_omschrijving):
    query = 'UPDATE categories SET omschrijving = ? WHERE category_id = ?;'
    conn = databaseinladen()
    try:
        conn.execute(query, (new_omschrijving, category_id))
        conn.commit()
    finally:
        conn.close()

def aantalnotities():
    query5 = 'SELECT COUNT(note_id) FROM notes;'
    conn = databaseinladen()
    result = conn.execute(query5).fetchone()
    count = result[0] if result else 0
    return count

def get_note_id(note_id):
    query = 'SELECT note_id, title, note, note_source, category_id FROM notes WHERE note_id=?;'
    conn = databaseinladen()
    cursor = conn.execute(query, (note_id,))
    note = cursor.fetchone()
    return note

def update_note(note_id,title,note,note_source,category_id):
    conn = databaseinladen()
    update_query = '''
    UPDATE notes
    SET title=?, note=?, note_source=?, category_id=?
    WHERE note_id=?
    '''

    conn.execute(update_query,(title,note,note_source,category_id,note_id))
    conn.commit()

def note(note_id):
    query2 = '''SELECT notes.note_id, notes.note, notes.title, notes.note_source, teachers.display_name, notes.date_created, categories.omschrijving FROM notes 
    INNER JOIN categories ON notes.category_id = categories.category_id 
    INNER JOIN teachers ON teachers.teacher_id = notes.teacher_id 
    WHERE notes.note_id=?;'''
    conn = databaseinladen()
    note_data = conn.execute(query2, (note_id,)).fetchone()

    if note_data:
        note_id, note, title, note_source, display_name, date_created, category_omschrijving = note_data

        question_query = 'SELECT exam_question FROM questions WHERE note_id = ?;'
        questions = conn.execute(question_query, (note_id,)).fetchall()

        return {
            'note_id': note_id,
            'note': note,
            'title': title,
            'note_source': note_source,
            'display_name': display_name,
            'date_created': date_created,
            'category_omschrijving': category_omschrijving,
            'questions': questions
        }
    else:
        return None

def save_question(note_id, exam_question):
    query = 'INSERT INTO questions (note_id, exam_question) VALUES (?,?)'
    conn = databaseinladen()
    conn.execute(query, (note_id, exam_question))
    conn.commit()

