from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request, json, redirect, url_for, session, jsonify
import psycopg2 as psql
import db_admin
import ast
import datetime
from dateutil.relativedelta import relativedelta

# Create flask app
app = Flask(__name__)

# Load the default configuration
app.config.from_object('config.DefaultConfig')

# Define the database object which is imported
# by modules and controllers
db = SQLAlchemy(app)

try:
    conn = psql.connect("dbname='postgres' user='postgres' host='localhost' password='19267686k'")
except psql.Error as e:
    print e.pgerror
    exit(1)
cur = conn.cursor()


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    user = request.form['user']
    password = request.form['password']
    cur.execute("SELECT username, password FROM users_not_encrypted WHERE username = %s", [user])
    result = cur.fetchall()
    if user is not None and password is not None and user != "" and password != "" \
            and len(result) > 0 and result[0][1] == password:
        session['username'] = user
        return json.dumps({"success": True})
    else:
        return json.dumps({"success": False})


@app.route('/home', methods=['POST', 'GET'])
def home():
    if len(session) > 0 and session['username'] is not None:
        cur.execute("select column_name from information_schema.columns "
                    "where table_name = 'info_users_not_encrypted'")
        summary_header = filter(lambda y: y != 'username', map(lambda x: x[0], cur.fetchall()))
        summary_header.insert(0, '#')
        cur.execute("SELECT * FROM info_users_not_encrypted WHERE username = %s", [session['username']])
        summary_result = cur.fetchall()
        summary_temp = list(summary_result[0])[1:]
        summary_temp.insert(0, 'Amount')
        summary_rows = [summary_temp]

        cur.execute("select * from transactions WHERE username = %s ORDER BY date_time limit 10", [session['username']])
        transactions_results = cur.fetchall()
        transactions_header = ["Transaction ID", "Date", ""]
        if transactions_results > 0:
            transactions_rows = map(lambda x: [x[0], x[1], x[0]], transactions_results)

        data = {
            "user": session['username'],
            "tables": [
                {
                    "name": "Summary",
                    "header": summary_header,
                    "rows": summary_rows,
                    "indexes": range(len(summary_rows[0]))}
            ],
            "especial_tables": {
                "transactions":
                    {
                        "name": "Transactions",
                        "header": transactions_header,
                        "rows": transactions_rows,
                        "indexes": range(3)
                    }
            }
        }
        return render_template("home.html", data=data)
    else:
        return render_template("404.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', connected=len(session) > 0 and session['username'] is not None), 404


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/transaction', methods=['POST', 'GET'])
def transaction():
    if len(session) > 0 and session['username'] is not None:
        cur.execute("select column_name from information_schema.columns "
                    "where table_name = 'info_users_not_encrypted'")
        result = filter(lambda y: y != 'username', map(lambda x: x[0], cur.fetchall()))
        data = map(lambda x: str(x), result)
        return render_template('transaction.html', data={"options": data})
    else:
        return render_template("404.html")


@app.route('/summit', methods=['POST', 'GET'])
def summit():
    data = request.form.to_dict()

    if len(data) > 0:
        pos = [data['lat'], data['lng']]
        form_data = data.copy()
        del form_data['lat']
        del form_data['lng']

        ver, pos_final = db_admin.transaction(data=form_data, user=session['username'], pos_in=pos)

        return render_template("summit.html", data={'details': [[key, value] for key, value in form_data.iteritems()],
                                                    'success': ver, 'pos_out': pos_final['pos'] if ver else None,
                                                    'pos_in': pos})
    else:
        return render_template("404.html")


@app.route('/trasaction_details/<int:transaction_id>')
def trasaction_details(transaction_id):
    cur.execute("select * from transactions WHERE id = %s AND username = %s", [transaction_id, session['username']])
    result = cur.fetchall()
    details_dict = ast.literal_eval(result[0][3])  # details

    cur.execute("select lat,lon from green_points WHERE id = %s", [result[0][6]])
    pos = cur.fetchall()[0]

    if result > 0:
        data = {
            "general": {
                "header": ["Transaction ID", "Date"],
                "rows": map(lambda x: [x[0], x[1]], result),
                "indexes": range(2)
            },
            "details": [[key, value] for key, value in details_dict.iteritems()],
            'pos_out': [pos[0], pos[1]],
            "pos_in": [result[0][4], result[0][5]]
        }
        return render_template("transaction_details.html", data=data)
    else:
        return render_template("404.html")


@app.route("/profile")
def profile():
    cur.execute("select username,email,user_type from users_not_encrypted WHERE username = %s", [session['username']])
    result = cur.fetchall()[0]
    keys = ["username", "email", "user_type"]
    data = {}
    for key, value in zip(keys, result):
        data[key] = value
    return render_template("profile.html", data=data)


@app.route("/stats")
def stats():
    cur.execute("select column_name from information_schema.columns "
                "where table_name = 'info_users_not_encrypted'")
    summary_header = filter(lambda y: y != 'username', map(lambda x: x[0], cur.fetchall()))
    cur.execute("SELECT * FROM info_users_not_encrypted WHERE username = %s", [session['username']])
    summary_result = cur.fetchall()
    summary_result = list(summary_result[0])[1:]
    material_data = []
    for name, value in zip(summary_header, summary_result):
        material_data.append([name, value])

    current_date = datetime.datetime.now().replace(microsecond=0)

    delta = relativedelta(months=+6)

    current_date_str = str(current_date)
    in_date_str = str(current_date - delta)

    last_six_months = {}  # included current month
    for i in range(0, 6):
        relative_date_temp = current_date - relativedelta(months=i)
        last_six_months[datetime.date(year=relative_date_temp.year, month=relative_date_temp.month, day=1)] = 0

    cur.execute("select date_time, details from transactions WHERE username = %s and date_time BETWEEN %s and %s",
                [session['username'], in_date_str, current_date_str])
    transactions_results = cur.fetchall()
    for date, details in transactions_results:
        dict_temp = ast.literal_eval(details)
        local_total = 0
        for key, value in dict_temp.iteritems():
            local_total += float(value)
        last_six_months[datetime.date(month=date.month, year=date.year, day=1)] += local_total

    time_data = {}
    xaxis = ['x']
    data_colums_time = ['Total']
    last_six_months_list = []

    for key, value in last_six_months.iteritems():
        last_six_months_list.append([key, value])

    last_six_months_list.sort(key=lambda x: x[1])

    for elem in last_six_months_list:
        xaxis.append(elem[0].strftime("%B - %Y"))
        data_colums_time.append(elem[1])

    time_data['x'] = xaxis
    time_data['data'] = data_colums_time
    data_colums_time_copy = list(data_colums_time)
    data_colums_time_copy[0] = "Total1"
    time_data['data1'] = data_colums_time_copy
    return render_template("stats.html", material_data=json.dumps(material_data), time_data=time_data)


if __name__ == "__main__":
    app.debug = True
    app.run()
