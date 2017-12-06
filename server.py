from bottle import Bottle, run, view, static_file, request, redirect
from database import Database

database = Database.getInstance()

app = Bottle()


@app.route('/')
@view('login.html')
def login():
    return {}

@app.route('/register')
@view('register.html')
def register():
    return {}

@app.route('/checklogin', method='POST')
def checklogin():
    username = request.forms.get('username')
    password = request.forms.get('password')
    realPasseword = database.getPassword(username)

    if password == realPasseword :
        return redirect('/home')
    else :
        return redirect('/')

@app.route('/saveregister', method='POST')
def saveregister():
    username = request.forms.get('username')
    password = request.forms.get('password')
    database.addUser(username, password)
    return redirect('/')


@app.route('/home')
@view('videogallery.html')
def home():
    return {}


@app.route('/static/<filename>')
def send_static(filename):
    return static_file(filename, root='./static')


run(app, host='localhost', port=8080)


