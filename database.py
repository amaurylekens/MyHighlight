from neo4j.v1 import GraphDatabase, basic_auth
import re


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
            driver = GraphDatabase.driver("bolt://localhost", auth=basic_auth("neo4j", "neo4j"))
            self.__session = driver.session()


    def addUser (self, username, password):
        request = "CREATE (:User {username : '" + username + "', password : '" + password + "'})"
        self.__session.run(request)

    def addTeam (self, name) :
        request = "CREATE (:Team {name : '" + name + "'})"
        self.__session.run(request)

    def addVideo (self, homeTeam, awayTeam, score, link) :
        goals = re.match("([0-9]+) ?- ?([0-9]+)", score)
        goalsHome = goals.group(1)
        goalsAway = goals.group(2)

        #create video entity
        request = "CREATE (:Video {goalsHome : '" + goalsHome + "', goalsAway : '" + goalsAway \
                  + "', link : '" + link + "'})"
        self.__session.run(request)

        #check if teams entity exist. If doesn't, create it
        request = "MATCH (t:Team {name : {name}})) RETURN t"
        teams = [homeTeam, awayTeam]

        for t in teams :
            result = self.__session.run(request, {'name' : t})
            try :
                t = result.single()
                print(t['t'].properties['name'], "déja créée")
            except :
                self.addTeam(t)

        #create link
        for t in teams :
            request = "CREATE (:Video {link: '" + link + "'}) -[:CONCERNS]-> (:Team {name : '" + t + "'})"
            self.__session.run(request)

    def addViewLinks (self, link, username):
        #create link user --> video, but before check if the link already exist
        request = "MATCH (:User {username : '" + username + "'})-[w:WATCH]-> " \
                                                        "(:Video {link: '" + link + "'}) SET w.number = w.number + 1"

        try:
            self.__session.run(request)
        except:
            request = "CREATE (:User {username : '" + username + "'})-[:WATCH {number : 1}]->" \
                                                                     "(:Video {link: '" + link + "'})"
            self.__session.run(request)

        #look to the concerned teams
        request = "MATCH (:Video {link : '" + link + "'}) -[CONCERNS]-> (t:Team) RETURN t.name"
        result = self.__session.run(request)

        teams = []
        for team in result.records():
            teams.append(team)

        #create the link user --> team, but before check if the link already exist
        for t in teams :
            # create link user --> video, but before check if the link already exist
            request = "MATCH (:User {username : '" + username + "'})-[w:WATCH]->(:Team {name: '" + t + "'}) " \
                                                                                        "SET w.number = w.number + 1"

            try:
                self.__session.run(request)
            except:
                request = "CREATE (:User {username : '" + username + "'})-[:WATCH {number : 1}]->" \
                                                                     "(:Team {name: '" + t + "'})"
                self.__session.run(request)

    def getPassword(self,username):
        request = "MATCH (u:User {username : '" + username + "'}) RETURN u"
        result = self.__session.run(request)
        try :
            u = result.single()
            password = u['u'].properties['password']
            return password
        except :
            return -1

    def close(self):
        self.__session.close()

