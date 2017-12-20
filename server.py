from flask import Flask, render_template, request, redirect, session
from database import Database

app = Flask(__name__)
app.secret_key = 'You Will Never Guess'
database = Database.getInstance()

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
    realPasseword = database.getPassword(username)

    if password == realPasseword :
        session['username'] = username
        session['nextVideosTeam'] = []
        return redirect('/home')
    else :
        return redirect('/')

@app.route('/saveregister', methods=['POST'])
def saveregister():
    username = request.form['username']
    password = request.form['password']
    database.addUser(username, password)
    return redirect('/')


@app.route('/home')
def home():
    nextVideos=[]
    if(session['nextVideosTeam'] != []):
        nextVideos = database.getNextVideos(session['nextVideosTeam'], session['username'])
    trendVideos = database.getTrendVideos()
    favoriteTeamVideos = database.getFavoriteTeamVideos(session['username'])
    allVideos = database.getAllVideos()
    return render_template("videogallery.html", trendVideos=trendVideos, allVideos=allVideos,
                           nextVideos=nextVideos, favoriteTeamVideos=favoriteTeamVideos)

@app.route('/admin', methods=['POST', 'GET'])
def admin():
    if isset('addTeam'):
        name = request.form['name']
        database.addTeam(name)
    elif isset('addVideo'):
        teamHome = request.form['team_home']
        teamAway = request.form['team_away']
        goalsHome = request.form['goals_home']
        goalsAway = request.form['goals_away']
        link = request.form['link']
        database.addVideo(teamHome, teamAway, goalsHome, goalsAway, link)
    teams = database.getTeams()
    return render_template("admin.html", teams=teams)

@app.route('/video', methods=['POST'])
def video():
    database.addViewLinks(request.form['link'], session['username'])
    session['nextVideosTeam'] = [request.form['teamHome'], request.form['teamAway']]
    return redirect('//www.youtube.com/embed/'+request.form['link'])




def isset(name):
    for elem in request.form:
        if elem == name :
            return True
    return False




if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=True)