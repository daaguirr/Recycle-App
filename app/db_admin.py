import os

import psycopg2 as psql
import datetime

try:
    conn = psql.connect("dbname='postgres' user='postgres' host='localhost' password='19267686k'")
except psql.Error as e:
    print e.pgerror
    exit(1)
cur = conn.cursor()


def add_user(username, password, email, user_type):
    cur.execute("INSERT INTO users_not_encrypted VALUES (%s,%s,%s,%s)", [username, password, email, user_type])
    cur.execute("INSERT INTO info_users_not_encrypted VALUES(%s)", [username])
    conn.commit()


def init_green_point():
    index = 1000000
    pos = [[-32.829981054721934, -70.60664176940918], [-32.83531792759262, -70.59853076934814],
           [-32.83077439395877, -70.59372425079346], [-32.83629151169454, -70.60376644134521],
           [-32.838202590180366, -70.59531211853027], [-32.83135136349751, -70.61479568481445],
           [-32.84375530177654, -70.6005048751831], [-32.84617098345136, -70.59655666351318],
           [-32.846819961352956, -70.59157848358154], [-32.842817855358895, -70.59544086456299],
           [-32.84375530177654, -70.60689926147461], [-32.84083476300433, -70.60702800750732],
           [-32.748590110255925, -70.73148250579834], [-32.74873448633906, -70.72564601898193],
           [-32.756133447289976, -70.72637557983398], [-32.75129712287589, -70.71689128875732],
           [-32.7453415865242, -70.72311401367188], [-32.74992558009646, -70.71504592895508],
           [-32.75544771577733, -70.72427272796631], [-32.73992711707743, -70.73186874389648],
           [-32.73963833613183, -70.7259464263916], [-32.74028809194337, -70.71684837341309],
           [-32.74259829645846, -70.71839332580566], [-32.76035599339278, -70.71925163269043],
           [-32.757901888402266, -70.71195602416992], [-32.753210028851896, -70.70500373840332]]

    for elem in pos:
        cur.execute("INSERT INTO green_points VALUES(%s,%s,%s)", [index, elem[0], elem[1]])
        index += 1
    conn.commit()


def transaction(data, user, pos_in):
    date = str(datetime.datetime.now().replace(microsecond=0))

    f = open("data/current_transaction", "r+")
    trans_id = int(f.read())
    f.close()
    f = open("data/current_transaction", "w+")
    f.write(str(trans_id + 1))
    f.close()

    comp = ""
    for name, amount in data.iteritems():
        comp += name + " is not null and "
        comp += "max_capacity_" + name + "-" + name + ">=" + str(amount) + " and "

    comp = comp[:-4]

    try:
        cur.execute("select id, (point(%s,%s) <@> point(t1.lat,t1.lon)) as distance, t1.lat, t1.lon "
                    "from (select * from green_points where " + comp + " ) as t1 order by distance;", [pos_in[0], pos_in[1]])

    except psql.Error as error:
        print error.pgerror
        return False, None

    results = cur.fetchall()

    if len(results) == 0:
        return False, None
    else:
        green_point_id = results[0][0]

        pos_out = [results[0][2], results[0][3]]
        cur.execute("INSERT INTO transactions  VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    [trans_id, date, user, str(data), pos_in[0], pos_in[1], green_point_id])
        add_string = ""
        for name, amount in data.iteritems():
            add_string += name + "=" + name + "+" + amount + " , "
        add_string = add_string[:-2]

        cur.execute("UPDATE green_points SET " + add_string + "WHERE id = %s", [green_point_id])
        cur.execute("UPDATE info_users_not_encrypted SET " + add_string + "WHERE username = %s", [user])
        conn.commit()
        return True, {'pos': pos_out}


def reset():
    # Delete Tables
    cur.execute("alter table info_users_not_encrypted drop constraint reference_key;")
    cur.execute("alter table transactions drop constraint reference_key_trans;")
    cur.execute("drop table users_not_encrypted;")
    cur.execute("drop table info_users_not_encrypted;")
    cur.execute("drop table transactions;")
    cur.execute("drop table green_points;")
    cur.execute("drop table material_list;")
    # Re - Create Tables
    cur.execute("create table users_not_encrypted(username varchar(32) primary key,password varchar(32) ,"
                "email varchar(64),user_type varchar(32));")
    cur.execute("create table info_users_not_encrypted(username varchar(32) primary key,pilas float DEFAULT 0.0,"
                "plastico float DEFAULT 0.0,papel float DEFAULT 0.0);")
    cur.execute("create table transactions(id int primary key,date_time TIMESTAMP(3),username varchar(32),"
                "details varchar(1024), source_place_lat float, source_place_lon float, reception_place_id int);")
    cur.execute("create table green_points(id int primary key,lat float,lon float,pilas float DEFAULT 0.0,"
                "plastico float DEFAULT 0.0,papel float DEFAULT 0.0,max_capacity_pilas float DEFAULT 50.0,"
                "max_capacity_plastico float DEFAULT 50.0,max_capacity_papel float DEFAULT 50.0);")
    cur.execute("create table material_list(id int primary key,name varchar(32));")
    # Add Constraint
    cur.execute("alter table info_users_not_encrypted add constraint reference_key foreign key(username) "
                "references users_not_encrypted(username);")
    cur.execute("alter table transactions add constraint reference_key_trans foreign key(username) "
                "references users_not_encrypted(username);")
    # Add Indexes
    cur.execute("create index user_transaction on transactions(username);")
    cur.execute("create index material_list_index on material_list using hash(name);")
    conn.commit()

    print os.getcwd()
    f = open("data/current_transaction", "w+")
    f.write(str(100000000))
    f.close()
    add_user("user", "1234", "example@bla.cl", 'user')
    init_green_point()

# reset()
