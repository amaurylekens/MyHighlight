from flask import Flask, render_template, request, redirect
from database import Database

app = Flask(__name__)
#database = Database.getInstance()

@app.route('/')
def login():
    return render_template("login.html")

@app.route('/register')
def register():
    return render_template("register.html")

@app.route('/checklogin', methods=['POST'])
def checklogin():
    username = request.form['username']
    password = request.form['password']
    #realPasseword = database.getPassword(username)

    """if password == realPasseword :
        return redirect('/home')
    else :
        return redirect('/')"""

@app.route('/saveregister', methods=['POST'])
def saveregister():
    username = request.form['username']
    password = request.form['password']
    #database.addUser(username, password)
    return redirect('/')


@app.route('/home')
def home():
    return render_template("videogallery.html")




if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=True)