from flask import Flask, render_template, request, url_for, redirect, session

import mysql.connector

from datetime import datetime,date,timedelta

connection = mysql.connector.connect(
    host='localhost',
    database='school',
    user='root',
    password='1234'
)


cursor = connection.cursor()
app = Flask(__name__)
app.secret_key = 'lol'


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute(
            "SELECT * FROM customers WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user:
            if password == user[1]:
                session['username'] = username
                return redirect(url_for('index'))
            else:
                error = 'Incorrect password. Please try again.'
                return render_template('register.html', error=error)

        else:
            cursor.execute(
                "INSERT INTO customers (username, password) VALUES (%s, %s)", (username, password))
            connection.commit()
            session['username'] = username
            return redirect(url_for('index'))

    return render_template('register.html')


@app.route("/", methods=['GET', 'POST'])
def index():

    if request.method == 'GET':
        username = session.get('username')

        cursor.execute(
            "SELECT * FROM hotels WHERE (Single_Room = 'Yes' OR Double_Room = 'Yes' OR Family_Room = 'Yes') ORDER BY RAND() LIMIT 10")
        hotels = cursor.fetchall()

        return render_template('index.html', hotels=hotels, username=username)

    if request.method == 'POST':
        username = session.get('username')

        destination = request.form['destination']
        cursor.execute(
            f"SELECT * FROM hotels WHERE (Single_Room = 'Yes' OR Double_Room = 'Yes' OR Family_Room = 'Yes') AND country = '{destination.upper()}' ORDER BY name")
        hotels = cursor.fetchall()
        return render_template('index.html', hotels=hotels, username=username)


@app.route("/details", methods=['POST', 'GET'])
def details():

    if request.method == "POST":
        check_in = request.form['check-in']

        check_out = request.form['check-out']
        hotel_id = request.form["hotel_id"]
        room = request.form['room']

        cursor.execute(
            "select name,country from hotels where hotel_id = %s", (hotel_id,))
        a = cursor.fetchone()

        o = datetime.strptime(check_out, '%Y-%m-%d').date()
        i = datetime.strptime(check_in, '%Y-%m-%d').date()
        days = (o - i).days
        
        if o == i:
            days = 1


        price = int(''.join(filter(str.isdigit, room))) * days

        cursor.execute("INSERT INTO confirm (username,hotel_id, hotel, country,check_in, check_out,room,price) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                       (session.get('username'), hotel_id, a[0], a[1], check_in, check_out, room, price))
        connection.commit()
        
        room_type = room[0:6] + '_'+room[7].upper()+room[8:11]
        
        cursor.execute(
            f"update hotels set {room_type} = 'No' where hotel_id = {hotel_id}")
        connection.commit()

        return redirect(url_for('user_bookings', username=session.get('username')))

    hotel_id = request.args.get('hotel_id')
    cursor.execute("select * from hotels where hotel_id = %s", (hotel_id,))
    details = cursor.fetchone()

    cursor.execute("Select * from confirm")
    bookings = cursor.fetchall()

    latest_date = date.today() + timedelta(days=1)
    

    cursor.execute(
        "Select Single_Room,Double_Room,Family_Room from hotels where hotel_id = %s", (hotel_id,))
    rooms = cursor.fetchone()

    return render_template('details.html', details=details, bookings=bookings, rooms=rooms, hotel_id=hotel_id,latest_date = latest_date)


@app.route("/user_bookings", methods=['GET'])
def user_bookings():
    if 'username' not in session:
        return redirect(url_for('register'))

    username = session['username']

    cursor.execute(
        "SELECT check_in, check_out , hotel, country , room , price FROM confirm WHERE username = %s", (username,))

    bookings = cursor.fetchall()

    return render_template('user_bookings.html', bookings=bookings)


@app.route("/cancel_booking", methods=['POST'])
def cancel_booking():
    if 'username' not in session:
        return redirect(url_for('register'))

    username = session['username']

    if request.method == "POST":
        hotel = request.form['hotel_name']
        room = request.form['room_type']

        cursor.execute(
            "DELETE FROM confirm WHERE username = %s AND hotel = %s AND room = %s", (username, hotel, room))
        connection.commit()

        room_type = room[0:6] + '_'+room[7].upper()+room[8:11]

        cursor.execute(
            f"Update hotels set {room_type} = 'Yes' where name = %s", (hotel,))
        connection.commit()

    return redirect(url_for('index'))


@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))
