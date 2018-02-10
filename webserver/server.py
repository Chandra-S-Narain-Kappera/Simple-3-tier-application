#!/usr/bin/env python2.7

"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver

To run locally:

    python server.py

Go to http://localhost:8111 in your browser.

A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@104.196.18.7/w4111
#
# For example, if you had username biliris and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://biliris:foobar@104.196.18.7/w4111"
#
DATABASEURI = "postgresql://ck2840:5623@104.196.18.7/w4111"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print ("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/

# Main Page
@app.route('/')
def main_page():
    print(request.args)
    return render_template("Main_Page.html")

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/another')
def another():
  return render_template("another.html")


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print ("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  # Example of adding new data to the database
  @app.route('/add', methods=['POST'])
  def add():
      name = request.form['name']
      g.conn.execute("""INSERT INTO test (name) VALUES ('""" + name + """"');""")
      return redirect('/')


  ## Sample executation of Pateints as a first step ##
  @app.route('/patient', methods=['POST', 'GET'])
  def patient():
      return render_template("patient.html")


  @app.route('/displayall', methods=['POST'])
  def displayall():
      cursor = g.conn.execute(""" Select * from patients;""")
      names = []
      rowcount = cursor.rowcount
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result2 = dict(data=names)

      admit = None
      pres = None


      return render_template("display_v2.html", admit=admit, pres=pres, **result2)


  @app.route('/display', methods=['POST'])
  def display():
      name = request.form['name']
      ssn = request.form['ssn']
      dname = request.form['dname']
      if len(name) > 1:
          cursor = g.conn.execute(""" Select * from patients where pname = '""" + name + """';""")
      elif len(ssn) > 1:
          cursor = g.conn.execute(""" Select * from patients where pssn = '""" + ssn + """';""")
      elif len(dname) > 1:
          cursor = g.conn.execute(""" Select p.pssn,p.pname, p.zip, p.age, p.dssn, p.disease from doctors d, patients p  where  d.dssn=p.dssn and d.dname='"""+dname+"""';""")

      names = []
      rowcount = cursor.rowcount
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result2 = dict(data=names)

      admit = None
      pres = None

      if  rowcount == 1:
          data = result2['data']
          pssn = data[0][0]


          cursor = g.conn.execute("""select p.pname as Name, d.dname as Doctor_Name, p.disease as Treatment, p.pssn as SSN, p.age as AGE, p.zip as ZIP from patients p JOIN  doctors d ON p.dssn=d.dssn where p.pssn='%s'""" % pssn)
          names = []
          rowcount = cursor.rowcount
          for result in cursor:
              names.append(result)  # can also be accessed using result[0]
          cursor.close()

          result2 = dict(data=names)
          # Admits table:
          admit = None
          cursor = g.conn.execute("""select a.rno as Room_No, a.indate as Indate, a.outdate as Outdate from patients p JOIN  admits a ON a.pssn=p.pssn  left outer JOIN incharge i ON i.rno=a.rno left outer JOIN nurses n ON n.nssn=i.nssn where p.pssn='%s'""" % pssn)
          if cursor.rowcount > 0:
              names = []
              rowcount = cursor.rowcount
              for result in cursor:
                  names.append(result)  # can also be accessed using result[0]
              admit = dict(data=names)
          cursor.close()

          # Prescription table
          pres = None
          cursor = g.conn.execute("""select d.dname as Doctor, pr.date as Date, pr.tradename as DrugName, pr.quantity as Quantity from patients p JOIN  prescription pr ON pr.pssn=p.pssn JOIN doctors d ON pr.dssn=d.dssn where p.pssn='%s'""" % pssn)
          if cursor.rowcount > 0:
              names = []
              rowcount = cursor.rowcount
              for result in cursor:
                  names.append(result)  # can also be accessed using result[0]
              pres = dict(data=names)
          cursor.close()

      return render_template("display_v2.html", admit=admit, pres=pres, **result2)


  @app.route('/addpatient', methods=['POST'])
  def addpatient():
      name = request.form['pname']
      ssn = request.form['pssn']
      zip = request.form['zip']
      age = request.form['age']
      dssn = request.form['dssn']
      disease = request.form['disease']
      str_input = "'" + ssn + "'," + "'" + name + "'," + "'" + str(zip) + "'," + "'" + str(
          age) + "'," + "'" + dssn + "'," + "'" + disease + "'"
      cursor = g.conn.execute("""INSERT INTO patients VALUES (""" + str_input + """);""")
      cursor = g.conn.execute("""SELECT * From patients;""")

      names = []
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result = dict(data=names)

      admit = None
      pres = None

      return render_template("display_v2.html", admit=admit, pres=pres, **result)


  @app.route('/delpatient', methods=['POST'])
  def delpatient():

      cursor = g.conn.execute("""DELETE FROM patients VALUES where pname='%s'""" % request.form['pname'])
      cursor = g.conn.execute("""SELECT * From patients;""")

      names = []
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result = dict(data=names)

      admit = None
      pres = None

      return render_template("display_v2.html", admit=admit, pres=pres, **result)

  @app.route('/updatepatient', methods=['POST'])
  def update_patient():

      name = request.form['pname']
      pssn = request.form['pssn']
      zip = request.form['zip']
      age = request.form['age']
      dssn = request.form['dssn']
      disease = request.form['disease']

      str_input = "UPDATE patients SET"
      if len(name) > 1:
          if(len(str_input) > 19):
              str_input += ""","""
          str_input += " pname='"+name+"'"
      if len(zip) > 1:
          if (len(str_input) > 19):
              str_input += ""","""
          str_input += " zip="+zip
      if len(age) > 1:
          if (len(str_input) > 19):
              str_input += ""","""
          str_input += " age=" + age
      if len(dssn) > 1:
          if (len(str_input) > 19):
              str_input += ""","""
          str_input += " dssn='"+dssn+"'"
      if len(disease) > 1:
          if (len(str_input) > 19):
              str_input += ""","""
          str_input += " disease='"+disease+"'"
      str_input += " where pssn='"+pssn+"';"
      cursor = g.conn.execute(str_input)
      cursor.close()
      cursor = g.conn.execute("""SELECT * From patients;""")

      names = []
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result = dict(data=names)

      admit = None
      pres = None

      return render_template("display_v2.html", admit=admit, pres= pres, **result)


# For Drugs:

  @app.route('/drug_add', methods=['POST'])
  def drug_add():
      name = request.form['tradename']
      formula = request.form['formula']
      company = request.form['company']
      str_input = "'" + name + "'," + "'" + formula + "'," + "'" + company + "'"
      cursor = g.conn.execute("""INSERT INTO drug VALUES (""" + str_input + """);""")
      cursor = g.conn.execute(""" Select d.tradename, d.formula, d.cname as company, c.phone from drug d JOIN company c ON d.cname=c.cname""")

      names = []
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result = dict(data=names)

      return render_template("display_v5.html", admit=None, pres=None, **result)


  @app.route('/drug', methods=['POST', 'GET'])
  def drug():
      return render_template("Drug.html")


  @app.route('/alldrugs', methods=['POST'])
  def alldrugs():

      cursor = g.conn.execute(
              """ Select d.tradename, d.formula, d.cname as company, c.phone from drug d JOIN company c ON d.cname=c.cname;""")

      names = []
      rowcount = cursor.rowcount
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result2 = dict(data=names)
      admit = None
      pres = None

      return render_template("display_v5.html", admit=admit, pres=pres, **result2)


  @app.route('/displaydrug', methods=['POST'])
  def displaydrug():
      name = request.form['tradename']
      formula = request.form['formula']
      company = request.form['company']
      if len(name) > 1:
          cursor = g.conn.execute(""" Select d.tradename, d.formula, d.cname as company, c.phone from drug d JOIN company c ON d.cname=c.cname where  d.tradename = '""" + name + """';""")
      elif len(formula) > 1:
          cursor = g.conn.execute(""" Select d.tradename, d.formula, d.cname as company, c.phone from drug d JOIN company c ON d.cname=c.cname where d.formula = '""" + formula + """';""")
      elif len(company) > 1:
          cursor = g.conn.execute(""" Select d.tradename, d.formula, d.cname as company, c.phone from drug d JOIN company c ON d.cname=c.cname where d.cname = '""" + company + """';""")

      names = []
      rowcount = cursor.rowcount
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result2 = dict(data=names)
      admit = None
      pres = None
      if rowcount == 1:
          data = result2['data']
          tradename = data[0][0]

          cursor=g.conn.execute(
                  """ Select d.tradename as name, d.formula as formula, d.cname as company, c.phone as phone from drug d JOIN company c ON d.cname=c.cname where d.tradename = '""" + tradename + """';""")
          names = []
          rowcount = cursor.rowcount
          for result in cursor:
              names.append(result)  # can also be accessed using result[0]
          cursor.close()

          result2 = dict(data=names)
          # Admits table:
          admit = None
          cursor = g.conn.execute(
              """select s.tradename as Name, s.phname as Pharmacy, s.price as Price from soldat s where s.tradename ='%s'""" % tradename)
          if cursor.rowcount > 0:
              names = []
              rowcount = cursor.rowcount
              for result in cursor:
                  names.append(result)  # can also be accessed using result[0]
              admit = dict(data=names)
          cursor.close()

          # Prescription table
          pres = None
          cursor = g.conn.execute(
              """select d.dname as Doctor, p.pname as Patient, pr.date as Date, pr.tradename as DrugName, pr.quantity as Quantity from patients p JOIN  prescription pr ON pr.pssn=p.pssn JOIN doctors d ON pr.dssn=d.dssn where pr.tradename='%s'""" % tradename)
          if cursor.rowcount > 0:
              names = []
              rowcount = cursor.rowcount
              for result in cursor:
                  names.append(result)  # can also be accessed using result[0]
              pres = dict(data=names)
          cursor.close()


      return render_template("display_v5.html", admit=admit, pres=pres, **result2)




  @app.route('/deldrug', methods=['POST'])
  def deldrug():

      cursor = g.conn.execute("""DELETE FROM drug VALUES where tradename='%s'""" % request.form['tradename'])
      cursor = g.conn.execute("""SELECT * From drug;""")

      names = []
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result = dict(data=names)

      return render_template("display_v5.html", admit=None, pres=None, **result)


  @app.route('/updatedrug', methods=['POST'])
  def update_drug():

      name = request.form['tradename']
      formula = request.form['forumla']
      company = request.form['company']

      str_input = "UPDATE drug SET"
      if len(name) > 1:
          if(len(str_input) > 15):
              str_input += ""","""
          str_input += " tradename='" + name + "'"
      if len(formula) > 1:
          if(len(str_input) > 15):
              str_input += ""","""
          str_input += " formula=" + formula
      if len(company) > 1:
          if(len(str_input) > 15):
              str_input += ""","""
          str_input += " cname=" + company
      str_input += " where tradename='" + name + "';"
      cursor = g.conn.execute(str_input)
      cursor.close()
      cursor = g.conn.execute("""SELECT * From drug;""")

      names = []
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result = dict(data=names)

      admit = None
      pres = None

      return render_template("display_v5.html", admit=admit, pres=pres, **result)


# Doctors:
  @app.route('/doctor', methods=['POST', 'GET'])
  def doctor():
      return render_template("doctor.html")


  @app.route('/alldoctors', methods=['POST', 'GET'])
  def alldoctors():

      cursor = g.conn.execute(""" Select dname, dssn, exp, speciality from doctors;""")

      names = []
      rowcount = cursor.rowcount
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result2 = dict(data=names)

      nurse = None
      pres = None

      return render_template("display_v3.html", pres=pres, nurse=nurse, **result2)


  @app.route('/displayv3', methods=['POST', 'GET'])
  def displayv3():
      name = request.form['dname']
      ssn = request.form['dssn']
      speciality = request.form['speciality']
      expirience1 = request.form['exp1']
      expirience2 = request.form['exp2']

      if len(name) > 1:
          cursor = g.conn.execute(""" Select dname, dssn, exp, speciality from doctors where dname = '""" + name + """';""")
      elif len(ssn) > 1:
          cursor = g.conn.execute(""" Select dname, dssn, exp, speciality from doctors where dssn = '""" + ssn + """';""")
      elif len(expirience1) > 0 and len(expirience2) > 0:
          cursor = g.conn.execute(""" Select dname, dssn, exp, speciality from doctors where  exp >="""+expirience1+"""and exp <= """ + expirience2+""";""")
      elif len(speciality) > 1:
          cursor = g.conn.execute(""" Select dname, dssn, exp, speciality from doctors where speciality = '""" + speciality + """';""")

      names = []
      rowcount = cursor.rowcount
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result2 = dict(data=names)

      nurse = None
      pres = None

      if  rowcount == 1:
          data = result2['data']
          ssn = data[0][1]

          # Prescription table:
          pres = None
          cursor = g.conn.execute("""select p.pname as Patient, pr.date as Date, pr.tradename as Drug, pr.quantity as Quantity from prescription pr JOIN doctors d ON d.dssn=pr.dssn JOIN patients p ON p.pssn=pr.pssn where d.dssn='%s'""" % ssn)
          if cursor.rowcount > 0:
              names = []
              for result in cursor:
                  names.append(result)  # can also be accessed using result[0]
              pres = dict(data=names)
          cursor.close()

          # Prescription table
          nurse = None
          cursor = g.conn.execute("""select p.pname as Patient, a.nname as Nurse from patients p JOIN doctors d ON d.dssn=p.dssn LEFT OUTER JOIN (select r.pssn as pssn, n.nname as nname from admits r JOIN incharge i ON i.rno=r.rno JOIN nurses n ON n.nssn=i.nssn) a ON p.pssn=a.pssn where d.dssn='%s'""" % ssn)
          if cursor.rowcount > 0:
              names = []
              rowcount = cursor.rowcount
              for result in cursor:
                  names.append(result)  # can also be accessed using result[0]
              nurse = dict(data=names)
          cursor.close()

      return render_template("display_v3.html", pres=pres, nurse=nurse, **result2)


  @app.route('/adddoctor', methods=['POST'])
  def adddoctor():
      name = request.form['dname']
      ssn = request.form['dssn']
      exp = request.form['exp']
      speciality = request.form['speciality']
      str_input = "'" + ssn + "'," + "'" + name + "','" + speciality+ "',"+exp
      cursor = g.conn.execute("""INSERT INTO doctors VALUES (""" + str_input + """);""")
      cursor = g.conn.execute(""" Select dname, dssn, exp, speciality from doctors ;""")

      names = []
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result = dict(data=names)

      nurse = None
      pres = None

      return render_template("display_v3.html", pres=pres, nurse=nurse, **result)


  @app.route('/addpres', methods=['POST'])
  def addpres():
      dssn = request.form['dssn']
      pssn = request.form['pssn']
      date = request.form['date']
      tradename = request.form['tradename']
      quantity = request.form['quantity']

      str_input = "'" + pssn + "'," + "'" + dssn + "'," +date+",'"+ tradename + "'," + quantity
      cursor = g.conn.execute("""INSERT INTO prescription VALUES (""" + str_input + """);""")
      cursor = g.conn.execute(""" Select dname, dssn, exp, speciality from doctors  where dssn = '"""+dssn+"""';""")

      names = []
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result2 = dict(data=names)

      pres = None
      cursor = g.conn.execute(
          """select p.pname as Patient, pr.date as Date, pr.tradename as Drug, pr.quantity as Quantity from prescription pr JOIN doctors d ON d.dssn=pr.dssn JOIN patients p ON p.pssn=pr.pssn where d.dssn='%s'""" % dssn)
      if cursor.rowcount > 0:
          names = []
          for result in cursor:
              names.append(result)  # can also be accessed using result[0]
          pres = dict(data=names)
      cursor.close()

      nurse = None

      return render_template("display_v3.html", pres=pres, nurse=nurse, **result2)


  @app.route('/deldoctor', methods=['POST'])
  def deldoctor():

      cursor = g.conn.execute("""DELETE FROM doctors VALUES where dname='%s'""" % request.form['dname'])
      cursor = g.conn.execute("""Select dname, dssn, exp, speciality from doctors;""")

      names = []
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result = dict(data=names)

      admit = None
      pres = None

      return render_template("display_v3.html", admit=admit, pres=pres, **result)

  @app.route('/updatedoctor', methods=['POST'])
  def update_doctor():

      dname = request.form['dname']
      dssn = request.form['dssn']
      speciality = request.form['speciality']
      exp = request.form['exp']

      str_input = "UPDATE doctors SET"
      if len(dssn) > 1:
          if(len(str_input) > 18):
              str_input += ""","""
          str_input += " dssn='"+dssn+"'"
      if len(dname) > 1:
          if(len(str_input) > 18):
              str_input += ""","""
          str_input += " dname='"+dname+"'"
      if len(exp) > 0:
          if(len(str_input) > 18):
              str_input += ""","""
          str_input += " exp=" + exp
      if len(speciality) > 1:
          if(len(str_input) > 18):
              str_input += ""","""
          str_input += " speciality='"+speciality+"'"
      str_input += " where dssn='"+dssn+"';"
      cursor = g.conn.execute(str_input)
      cursor.close()
      cursor = g.conn.execute("""SELECT * From doctors;""")

      names = []
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result = dict(data=names)

      nurse = None
      pres = None

      return render_template("display_v3.html", pres=pres, nurse=nurse, **result)

# Nurses

  @app.route('/nurse', methods=['POST', 'GET'])
  def nurse():
      return render_template("nurse.html")


  @app.route('/allnurses', methods=['POST', 'GET'])
  def allnurses():

      cursor = g.conn.execute(
              """ Select n.nname, n.nssn, i.rno from nurses n left outer JOIN incharge i on i.nssn=n.nssn;""")
      names = []
      rowcount = cursor.rowcount
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result2 = dict(data=names)

      patient = None
      doctor = None

      return render_template("display_v4.html", patient=patient, doctor=doctor, **result2)


  @app.route('/displayv4', methods=['POST', 'GET'])
  def displayv4():
      name = request.form['nname']
      ssn = request.form['nssn']
      dname = request.form['dname']
      pname = request.form['pname']
      rno = request.form['rno']

      if len(name) > 1:
          cursor = g.conn.execute(
              """ Select n.nname, n.nssn, i.rno from nurses n left outer JOIN incharge i on i.nssn=n.nssn where n.nname = '""" + name + """';""")
      elif len(ssn) > 1:
          cursor = g.conn.execute(
              """ Select n.nname, n.nssn, i.rno from nurses n left outer JOIN incharge i on i.nssn=n.nssn where n.nssn = '""" + ssn+ """';""")
      elif len(dname) > 1:
          cursor = g.conn.execute(
              """ Select n.nname, n.nssn, i.rno from nurses n left outer JOIN incharge i on i.nssn=n.nssn where n.nssn IN ( select i2.nssn from patients p1 JOIN doctors d1 ON d1.dssn=p1.dssn JOIN admits a2 ON a2.pssn=p1.pssn JOIN incharge i2 ON i2.rno=a2.rno where d1.dname = '%s');""" %dname)
      elif len(pname) > 1:
          cursor = g.conn.execute(
              """ Select n.nname, n.nssn, i.rno from nurses n left outer JOIN incharge i on i.nssn=n.nssn where n.nssn IN ( select i2.nssn from patients p1 JOIN doctors d1 ON d1.dssn=p1.dssn JOIN admits a2 ON a2.pssn=p1.pssn JOIN incharge i2 ON i2.rno=a2.rno where p1.pname = '%s');""" %pname)
      elif len(rno) > 0:
          cursor = g.conn.execute(
              """ Select n.nname, n.nssn, i.rno from nurses n left outer JOIN incharge i on i.nssn=n.nssn where i.rno ="""+rno+""";""")

      names = []
      rowcount = cursor.rowcount
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result2 = dict(data=names)

      patient = None
      doctor = None

      if rowcount == 1:
          data = result2['data']
          ssn = data[0][1]

          # Patient name:
          patient = None
          cursor = g.conn.execute(
              """Select p1.pname from patients p1 JOIN doctors d1 ON d1.dssn=p1.dssn JOIN admits a2 ON a2.pssn=p1.pssn JOIN incharge i2 ON i2.rno=a2.rno where i2.nssn = '%s';""" %ssn)
          if cursor.rowcount > 0:
              names = []
              for result in cursor:
                  names.append(result)  # can also be accessed using result[0]
              patient = dict(data=names)
          cursor.close()

          # Doctor table
          doctor = None
          cursor = g.conn.execute(
              """Select d1.dname from patients p1 JOIN doctors d1 ON d1.dssn=p1.dssn JOIN admits a2 ON a2.pssn=p1.pssn JOIN incharge i2 ON i2.rno=a2.rno where i2.nssn = '%s';""" %ssn)
          if cursor.rowcount > 0:
              names = []
              rowcount = cursor.rowcount
              for result in cursor:
                  names.append(result)  # can also be accessed using result[0]
              doctor = dict(data=names)
          cursor.close()

      return render_template("display_v4.html", patient=patient, doctor=doctor, **result2)


  @app.route('/addnurse', methods=['POST'])
  def addnurse():
      name = request.form['nname']
      ssn = request.form['nssn']
      rno = request.form['rno']
      str_input = "'" + name + "'," + "'" + ssn+"'"
      cursor = g.conn.execute("""INSERT INTO nurses VALUES (""" + str_input + """);""")
      cursor.close()
      str_input = "'" + ssn + "'," + "'" + rno + "'"
      cursor = g.conn.execute("""INSERT INTO incharge VALUES (""" + str_input + """);""")
      cursor.close()
      cursor = g.conn.execute(
          """ Select n.nname, n.nssn, i.rno from nurses n left outer JOIN incharge i on i.nssn=n.nssn ;""")

      names = []
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result = dict(data=names)

      patient = None
      doctor = None

      return render_template("display_v4.html", patient=patient, doctor=doctor, **result)


  @app.route('/delnurse', methods=['POST'])
  def delnurse():

      cursor = g.conn.execute("""DELETE FROM nurses VALUES where nname='%s'""" % request.form['nname'])
      cursor = g.conn.execute(
          """ Select n.nname, n.nssn, i.rno  from nurses n left outer JOIN incharge i on i.nssn=n.nssn ;""")

      names = []
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result = dict(data=names)

      patient = None
      doctor = None

      return render_template("display_v4.html", patient=patient, doctor=doctor, **result)


  @app.route('/updatenurse', methods=['POST'])
  def update_nurse():

      nname = request.form['nname']
      nssn = request.form['nssn']
      rno = request.form['rno']

      str_input = "UPDATE nurses SET"
      if len(nssn) > 1:
          if (len(str_input) > 17):
              str_input += ""","""
          str_input += " nssn='" + nssn + "'"
      if len(nname) > 1:
          if (len(str_input) > 17):
              str_input += ""","""
          str_input += " nname='" + nname + "'"
      str_input += " where nssn='" + nssn + "';"
      cursor = g.conn.execute(str_input)
      cursor.close()

      str_input = "select * from incharge where nssn='"+nssn+"';"
      cursor = g.conn.execute(str_input)
      rowcount = cursor.rowcount
      names = []
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result3 = dict(data=names)
      cursor.close()
      if( rowcount == 0):
          str_input = "'" + nssn + "'," + "'" + rno + "'"
          cursor = g.conn.execute("""INSERT INTO incharge VALUES (""" + str_input + """);""")
          cursor.close

      if rowcount > 0:
          data = result3['data']
          rrno = data[0][1]
      elif rowcount == 0:
          rrno = rno

      str_input = "UPDATE incharge SET"
      if len(nssn) > 0:
          if (len(str_input) > 19):
              str_input += ""","""
          str_input += " nssn='" + nssn + "'"
      if len(rno) > 0:
          if (len(str_input) > 19):
              str_input += ""","""
          str_input += " rno='" + rno + "'"
      str_input += " where nssn='" + nssn +"' and rno="+str(rrno)+";"
      cursor = g.conn.execute(str_input)
      cursor.close()

      cursor = g.conn.execute(
          """ Select n.nname, n.nssn, i.rno from nurses n left outer JOIN incharge i on i.nssn=n.nssn ;""")

      names = []
      for result in cursor:
          names.append(result)  # can also be accessed using result[0]
      cursor.close()

      result = dict(data=names)

      patient = None
      doctor = None

      return render_template("display_v4.html", patient=patient, doctor=doctor, **result)


  @app.errorhandler(500)
  def internal_server_error(e):
      return render_template('Error.html', error=e), 500

  run()
