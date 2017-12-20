from neo4j.v1 import GraphDatabase, basic_auth
from time import time, mktime
from datetime import datetime, timedelta


class Database :
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if Database.__instance == None:
            Database()
        return Database.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if Database.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            Database.__instance = self
            self.__driver = GraphDatabase.driver("bolt://localhost", auth=basic_auth('amaury', 'amaury'))


    def addUser (self, username, password):
        request = "CREATE (:User {username : '" + username + "', password : '" + password + "'})"
        session = self.__driver.session()
        session.run(request)

    def addTeam (self, name) :
        request = "CREATE (:Team {name : '" + name + "'})"
        session = self.__driver.session()
        session.run(request)

    def addVideo (self, homeTeam, awayTeam, goalsHome, goalsAway, link) :
        #create video entity
        date = str(int(time()))
        request = "CREATE (:Video {link : '" + link + "', goalsHome : '" + goalsHome \
                  + "', goalsAway : '" + goalsAway + "', homeTeam : '" + homeTeam + \
                  "', awayTeam : '" + awayTeam + "', date : " + date + "})"
        session = self.__driver.session()
        session.run(request)

        teams = [homeTeam, awayTeam]

        #create link
        for t in teams:
            request = "MATCH (v:Video {link: '" + link + "'}) "
            request += "MATCH (t:Team {name : '" + t + "'})"
            request += "CREATE (v) -[:CONCERNS]-> (t)"
            session = self.__driver.session()
            session.run(request)

    def getTeams(self):
        request = "MATCH (t:Team) RETURN t"
        session = self.__driver.session()
        result = session.run(request)

        teams = []
        for team in result.records():
            teams.append(team['t'].properties['name'])

        return teams


    def addViewLinks (self, link, username):
        #create link user --> video, but before check if the link already exist
        request = "MATCH (:User {username : '" + username + "'})-[w:WATCH]-> " \
                                         "(:Video {link: '" + link + "'}) SET w.number = w.number + 1 RETURN w"
        session = self.__driver.session()
        result = session.run(request)

        if result.single() == None:
            print("hello")
            request = "MATCH (u:User {username : '" + username + "'})\
                       MATCH (v:Video {link: '" + link + "'})\
                       CREATE (u)-[:WATCH {number : 1}]->(v)"
            session = self.__driver.session()
            session.run(request)

        #look to the concerned teams
        request = "MATCH (:Video {link : '" + link + "'}) -[CONCERNS]-> (t:Team) RETURN t"
        session = self.__driver.session()
        result = session.run(request)

        teams = []
        for team in result.records():
            teams.append(team['t'].properties['name'])

        #create the link user --> team, but before check if the link already exist
        for t in teams :
            # create link user --> video, but before check if the link already exist
            request = "MATCH (:User {username : '" + username + "'})-[w:WATCH]->(:Team {name: '" + t + "'}) " \
                                                                    "SET w.number = w.number + 1 RETURN w"
            session = self.__driver.session()
            result = session.run(request)
            if result.single() == None:
                request = "MATCH (u:User {username : '" + username + "'})\
                           MATCH (t:Team {name: '" + t + "'})\
                           CREATE (u)-[:WATCH {number : 1}]->(t)"
                session = self.__driver.session()
                session.run(request)

    def getPassword(self,username):
        request = "MATCH (u:User {username : '" + username + "'}) RETURN u"
        session = self.__driver.session()
        result = session.run(request)
        try :
            u = result.single()
            password = u['u'].properties['password']
            return password
        except :
            return -1

    def getAllVideos(self):
        request = "MATCH (v:Video) RETURN v"
        session = self.__driver.session()
        result = session.run(request)

        videos = []
        for v in result.records():
            video = {}
            video['link'] = v['v'].properties['link']
            video['goalsHome'] = v['v'].properties['goalsHome']
            video['goalsAway'] = v['v'].properties['goalsAway']
            video['teamHome'] = v['v'].properties['homeTeam']
            video['teamAway']= v['v'].properties['awayTeam']
            videos.append(video)

        return videos

    def getTrendVideos(self):
        # get all 5-day old videos
        limitDate = (datetime(datetime.now().year, datetime.now().month, datetime.now().day)-timedelta(3)).timestamp()
        request =  "MATCH (v:Video) "
        request += "WHERE v.date>" + str(int(limitDate)) + " "
        request += "MATCH (:User)-[w:WATCH]->(v)"
        request += "RETURN v, sum(w.number) AS n"
        session = self.__driver.session()
        result = session.run(request)

        # associate the video nodes and the number of view in a tupple
        videos= []
        for video in result.records():
            videos.append((video['n'], video['v']))

        # sort by number of view descending
        videos = sorted(videos, key=lambda colon: colon[0])
        videos = list(reversed(videos))

        # get five video
        videosSelected = []
        try :
            for i in range(5):
                video = {}
                video['link'] = videos[i][1].properties['link']
                video['goalsHome'] = videos[i][1].properties['goalsHome']
                video['goalsAway'] = videos[i][1].properties['goalsAway']
                video['teamHome'] = videos[i][1].properties['homeTeam']
                video['teamAway'] = videos[i][1].properties['awayTeam']
                videosSelected.append(video)
        except IndexError:
            pass

        return videosSelected


    def getNextVideos(self, teams, username):
        # find the favorite (the team wi’th the most views of the user) team in teams
        numbersOfViews = {}
        for team in teams :
            request = "MATCH (:User {username:'" + username + "'})-[w:WATCH]->(:Team {name : '" + team + "'}) RETURN w"
            session = self.__driver.session()
            result = session.run(request)
            w = result.single()
            numbersOfViews[team] = w['w'].properties['number']
        favoriteTeam = ""
        max = 0
        for team in teams :
            if numbersOfViews[team] > max :
                max = numbersOfViews[team]
                favoriteTeam = team

        # get all the videos of the favorite team
        request = "MATCH (v:Video)-[:CONCERNS]->(:Team {name : '" + favoriteTeam + "'}) "
        request += "MATCH (:User)-[w:WATCH]->(v) "
        request += "RETURN v, sum(w.number) AS n"
        session = self.__driver.session()
        result = session.run(request)

        # associate the video nodes and the number of view in a tupple
        videos = []
        for video in result.records():
            videos.append((video['n'], video['v']))

        # sort by number of view descending
        videos = sorted(videos, key=lambda colon: colon[0])
        videos = list(reversed(videos))

        # get five video
        videosSelected = []
        try:
            for i in range(5):
                video = {}
                video['link'] = videos[i][1].properties['link']
                video['goalsHome'] = videos[i][1].properties['goalsHome']
                video['goalsAway'] = videos[i][1].properties['goalsAway']
                video['teamHome'] = videos[i][1].properties['homeTeam']
                video['teamAway'] = videos[i][1].properties['awayTeam']
                videosSelected.append(video)
        except IndexError:
            pass

        return videosSelected

    def getFavoriteTeamVideos(self, username):
        # get all the team and the number of time that the user watch it
        request = "MATCH (:User {username:'" + username + "'})-[w:WATCH]->(t:Team) RETURN w.number AS w, t.name AS t"
        session = self.__driver.session()
        result = session.run(request)
        favoriteTeam = ""

        # find the favorite team (the most watched)
        max = 0
        for team in result.records():
            if team['w'] > max:
                max = team['w']
                favoriteTeam = team['t']

        # get all the videos of the favorite team
        request = "MATCH (v:Video)-[:CONCERNS]->(:Team {name : '" + favoriteTeam + "'}) "
        request += "MATCH (:User)-[w:WATCH]->(v) "
        request += "RETURN v, sum(w.number) AS n"
        session = self.__driver.session()
        result = session.run(request)

        # associate the video nodes and the number of view in a tupple
        videos = []
        for video in result.records():
            videos.append((video['n'], video['v']))

        # sort by number of view descending
        videos = sorted(videos, key=lambda colon: colon[0])
        videos = list(reversed(videos))

        # get five video
        videosSelected = []
        try:
            for i in range(5):
                video = {}
                video['link'] = videos[i][1].properties['link']
                video['goalsHome'] = videos[i][1].properties['goalsHome']
                video['goalsAway'] = videos[i][1].properties['goalsAway']
                video['teamHome'] = videos[i][1].properties['homeTeam']
                video['teamAway'] = videos[i][1].properties['awayTeam']
                videosSelected.append(video)
        except IndexError:
            pass

        return videosSelected


    def close(self):
        session = self.__driver.session()
        session.close()

