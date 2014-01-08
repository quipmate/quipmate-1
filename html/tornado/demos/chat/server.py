import sys
sys.path.append('/var/www/common/')
import secret
import hashlib
import tornado.database
import time
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import os.path
import tornado.httpclient
from HTMLParser import HTMLParser
from tornado.options import define, options
global cursorDict
cursorDict = {}

define("port", default=8888, help="Server Port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/chat/online", OnlineHandler),
			(r"/chat/typing_new", ChatTypingNewHandler),
			(r"/chat/chat_seen", ChatSeenHandler),
            (r"/chat/chat_new", ChatNewHandler),
            (r"/chat/chat_update", ChatUpdateHandler),
            (r"/chat/real_time", RealTimeHandler),
			(r"/chat/offline", OfflineHandler),
        ]
        settings = dict(
            cookie_secret="43oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            login_url="/auth/login",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=False,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class Database(tornado.database.Connection):
    def connect(self):
	tornado.database.Connection.__init__(self, secret.DB_IP, self.DB_NAME, user = secret.DB_USER, password= secret.DB_PASSWORD)
	return self._cursor()

    def query(self,query,cursor):
        cursor.execute(query)
        #self.close()
        return cursor 

class Query(Database):

    def chat_select(self, user, time):
        global cursorDict
	if cursorDict.has_key(self.DB_NAME) == False:
		cursor = self.connect()
		cursorDict[self.DB_NAME] = cursor
	else:
		cursor = cursorDict[self.DB_NAME]
        sql_query = "select * from inbox where (ACTIONBY = '%s' or ACTIONON = '%s') and time > '%s' order by ACTIONID desc limit 4" %(user, user, time)
        return self.query(sql_query, cursor)

    def get_globalid(self):	
	global cursorDict
	if cursorDict.has_key(self.DB_NAME) == False:
		cursor = self.connect()
		cursorDict[self.DB_NAME] = cursor
	else:
		cursor = cursorDict[self.DB_NAME]
	sql_query = "REPLACE INTO globalid (stub) VALUES ('a')"
	cursor.execute(sql_query)
	sql_query = "SELECT LAST_INSERT_ID() as id"
	return self.query(sql_query,cursor)
	
    def chat_insert(self, actionid, sentby, sentto, message, time):
	global cursorDict
	if cursorDict.has_key(self.DB_NAME) == False:
		cursor = self.connect()
		cursorDict[self.DB_NAME] = cursor
	else:
		cursor = cursorDict[self.DB_NAME]
	message = message.replace("'","\\'")
        sql_query = r"insert into inbox(ACTIONID, ACTIONBY, ACTIONON, MESSAGE, TIME) values( '%s', '%s', '%s', '%s', '%s')" %(actionid, sentby, sentto, message, time)
	return self.query(sql_query, cursor)

    def name_select(self, profileid):
        global cursorDict
	if cursorDict.has_key(self.DB_NAME) == False:
		cursor = self.connect()
		cursorDict[self.DB_NAME] = cursor
	else:
		cursor = cursorDict[self.DB_NAME]
        sql_query = "select NAME from bio where PROFILEID = '%s' " %(profileid)
        return self.query(sql_query, cursor)

    def photo_select(self, profileid):
        global cursorDict
	if cursorDict.has_key(self.DB_NAME) == False:
		cursor = self.connect()
		cursorDict[self.DB_NAME] = cursor
	else:
		cursor = cursorDict[self.DB_NAME]
        sql_query = "select CDN,FILENAME from profile_image where PROFILEID = '%s' order by imageid desc limit 1" %(profileid)
        return self.query(sql_query, cursor)

    def online_select(self, profileid):
        global cursorDict
	if cursorDict.has_key(self.DB_NAME) == False:
		cursor = self.connect()
		cursorDict[self.DB_NAME] = cursor
	else:
		cursor = cursorDict[self.DB_NAME]
        sql_query = "SELECT friend.FRIENDID,callback FROM friend inner join online ON friend.FRIENDID = online.profileid WHERE friend.PROFILEID = '%s' and online.time <> '0' " %(profileid)
        return self.query(sql_query, cursor)

    def online_replace(self, profileid, time, callback=""):
        global cursorDict
	if cursorDict.has_key(self.DB_NAME) == False:
		cursor = self.connect()
		cursorDict[self.DB_NAME] = cursor
	else:
		cursor = cursorDict[self.DB_NAME]
        sql_query = "replace into online(profileid, callback, time) values( '%s', '%s', '%s')" %(profileid, callback, time)
        return self.query(sql_query, cursor)

    def new_action_select(self, profileid, last_poll_time):
        global cursorDict
	if cursorDict.has_key(self.DB_NAME) == False:
		cursor = self.connect()
		cursorDict[self.DB_NAME] = cursor
	else:
		cursor = cursorDict[self.DB_NAME]
        sql_query = "select a.* from action as a inner join subscribe as sub on CASE WHEN a.PROFILEID <1000000000 THEN a.PROFILEID ELSE a.ACTIONBY END = sub.FRIENDID inner join actiontype on actiontype.actiontypeid = a.ACTIONTYPE where sub.PROFILEID='%s' and actiontype.live_feed ='1' and unix_timestamp(a.TIMESTAMP) > '%s' order by a.ACTIONID desc limit 50" %(profileid, last_poll_time)
        return self.query(sql_query, cursor)
		
    def new_event_test(self, profileid, time):
	global cursorDict
	if cursorDict.has_key(self.DB_NAME) == False:
		cursor = self.connect()
		cursorDict[self.DB_NAME] = cursor
	else:
		cursor = cursorDict[self.DB_NAME]
	sql_query = "select unix_timestamp(action.TIMESTAMP) from action inner join friend on action.ACTIONBY = friend.FRIENDID where friend.PROFILEID='%s' and actiontype not in('51','1151') and unix_timestamp(action.TIMESTAMP) > '%s' order by action.ACTIONID desc limit 1" %(profileid, time)
	cursor = self.query(sql_query, cursor)
	if cursor.rowcount == 0:
		return cursor.rowcount
	else:
		for row in cursor:
			return row[0]	
	    
    def notice_unread_count(self, profileid):
	global cursorDict
	if cursorDict.has_key(self.DB_NAME) == False:
		cursor = self.connect()
		cursorDict[self.DB_NAME] = cursor
	else:
		cursor = cursorDict[self.DB_NAME]
	sql_query = "select count(*),unix_timestamp(TIMESTAMP) from notice where READBIT ='0' and PROFILEID = '%s' and ACTIONBY <> '%s' and ACTIONTYPE <> '401' order by ACTIONID desc limit 1" %(profileid, profileid)
	return self.query(sql_query, cursor)	
	
    def unread_count(self, profileid):
	global cursorDict
	if cursorDict.has_key(self.DB_NAME) == False:
		cursor = self.connect()
		cursorDict[self.DB_NAME] = cursor
	else:
		cursor = cursorDict[self.DB_NAME]
	sql_query = "select count(*) from inbox where READBIT ='0' and ACTIONON = '%s' group by ACTIONBY" %(profileid)
	return self.query(sql_query, cursor)

    def request_unread_count(self, profileid, actiontype1, actiontype2, actiontype3):
	global cursorDict
	if cursorDict.has_key(self.DB_NAME) == False:
		cursor = self.connect()
		cursorDict[self.DB_NAME] = cursor
	else:
		cursor = cursorDict[self.DB_NAME]
	sql_query = "select count(*) from notice where READBIT ='0' and PROFILEID = '%s' and (ACTIONTYPE = '%s' or ACTIONTYPE = '%s' or ACTIONTYPE = '%s') " %(profileid, actiontype1, actiontype2, actiontype3)
	return self.query(sql_query, cursor)

    def offline_replace(self, time):
        global cursorDict
	if cursorDict.has_key(self.DB_NAME) == False:
		cursor = self.connect()
		cursorDict[self.DB_NAME] = cursor
	else:
		cursor = cursorDict[self.DB_NAME]
        sql_query = "update online set time = 0 where time < '%s' " %(time)
        return self.query(sql_query, cursor)

    def chat_readbit_update(self, sentby, sentto):
        global cursorDict
	if cursorDict.has_key(self.DB_NAME) == False:
		cursor = self.connect()
		cursorDict[self.DB_NAME] = cursor
	else:
		cursor = cursorDict[self.DB_NAME]
        sql_query = "update inbox set READBIT ='1' where ACTIONBY='%s' and ACTIONON='%s'" %(sentby, sentto)
        return self.query(sql_query, cursor)
		
class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

class BaseHandler(tornado.web.RequestHandler, Query):
    def get_name(self, profileid):
        cursor = self.name_select(profileid)
        for row in cursor:                 
            return row[0]
         
    def get_photo(self, profileid):
        cursor = self.photo_select(profileid)
        for row in cursor:      
            return row[0]+row[1]	

class RealTimeHandler(BaseHandler):

    @tornado.web.asynchronous
    def post(self):
		self.DB_NAME = self.get_argument("database")
		self.new_action(self.get_argument("database"),self.get_argument("profileid"), self.ret_rtm, self.get_argument("last_poll_time"))

    def new_action(self, database, profileid, callback, last_poll_time):
		count = 0
		message_count = 0
		request_count = 0
		response = 0
		action = []
		ack = 0
		if last_poll_time == '-1':
			cursor = self.notice_unread_count(profileid)
			rows = cursor.fetchall()
			for row in rows:
				count = row[0]
				ack = 1
				
			cursor = self.unread_count(profileid)
			rows = cursor.fetchall()
			for row in rows:
				message_count = row[0]
				ack = 1

			cursor = self.request_unread_count(profileid,7,501,408)
			rows = cursor.fetchall()
			for row in rows:
				request_count = row[0]
				ack = 1				
			if ack ==1:
				last_poll_time = time.time()
				try:	
					callback(response, count, message_count, request_count, database, profileid, action, last_poll_time)
				except:
					pass
			else:
				print "Error in executing db query"		
		else:
			test = self.new_event_test(profileid, last_poll_time)
			if test == 0:
			   tornado.ioloop.IOLoop.instance().add_timeout(time.time()+5, lambda:callback(response, count, message_count, request_count, database, profileid, action, last_poll_time, flag=1))
			else:
				cursor = self.notice_unread_count(profileid)
				rows = cursor.fetchall()
				for row in rows:
					count = row[0]
					ack = 1
		
				cursor = self.unread_count(profileid)
				rows = cursor.fetchall()
				for row in rows:
					message_count = row[0]
					ack = 1

				cursor = self.request_unread_count(profileid,7,501,408)
				rows = cursor.fetchall()
				for row in rows:
					request_count = row[0]
					ack = 1				
														
				cursor = self.new_action_select(profileid, last_poll_time)
				rows = cursor.fetchall()
				for row in rows:
					mydict = {}
					mydict['pageid'] =str(row[2])
					mydict['actionby'] = str(row[3])
					mydict['actionid'] = str(row[1])
					mydict['actionon'] = str(row[0])
					mydict['actiontype'] = str( row[4])
					m = hashlib.sha1()
					m.update(str(row[2])+"pass1reset!")
					mydict['life_is_fun'] =m.hexdigest()
					action.append(mydict)
					ack = 1 
				url = "http://50.57.190.112/ajax/news_json.php?polling=polling&database="+database+"&profileid="+profileid+"&last_poll_time="+last_poll_time
				http_client = tornado.httpclient.HTTPClient()
				try:
					response = http_client.fetch(url)
				except httpclient.HTTPError as e:
					print "Error:", e
				http_client.close()				
				if ack ==1:
					last_poll_time = time.time();
					try:	
						callback(response, count, message_count, request_count, database, profileid, action, last_poll_time)
					except:
						pass
               			
	
    def ret_rtm(self, response, count, message_count, request_count, database, profileid, action, last_poll_time, flag=0):
		if flag == 1:
		   return self.new_action(database, profileid, self.ret_rtm, last_poll_time)
		name = {}
		photo = {}
		if self.request.connection.stream.closed():
			return	
		for i in action:
			if i['actionby'] not in name:
				name[i['actionby']] = self.get_name(i['actionby'])
				photo[i['actionby']] = self.get_photo(i['actionby'])
			if i['actionon'] not in name:
				name[i['actionon']] = self.get_name(i['actionon'])
				photo[i['actionon']] = self.get_photo(i['actionon']) 
		try:
		   news = {}	
		   if response != 0:
				news = response.body
		   self.finish(dict(response=news, count=count, message_count=message_count, request_count=request_count, action=action, name=name,photo=photo, last_poll_time=last_poll_time))
		except Exception,e:
			   print e							

class ChatMixin(tornado.web.RequestHandler, Query):
   listener = {}
   def wait(self,database,user,callback):
	   cm = ChatMixin	
	   cm.listener[callback] = database+'_'+user
	   
   def seen(self,chat,name,photo,database):
		cm = ChatMixin
		photo = ""
		action = []
                d = dict(cm.listener)
		for i,v in cm.listener.iteritems(): 
		   if v == database+'_'+chat['sentby']:
                          del d[i]
			  action.append(chat)		  
			  i(action,name,photo)
                cm.listener = d			   
	   
   def typing(self,chat,name,photo,database):
		cm = ChatMixin
		photo = ""
		action = []
                d = dict(cm.listener)
		for i,v in cm.listener.iteritems(): 
		   if v == database+'_'+chat['sentto']:
                          del d[i]
			  action.append(chat)						  
			  i(action,name,photo)
                cm.listener = d		   
       	
   def message(self,chat,name,photo,database):
		cm = ChatMixin
		action = []
                d = dict(cm.listener)
		for i,v in cm.listener.iteritems(): 
		   if v == database+'_'+chat['sentto']:
                          del d[i]
			  action.append(chat)
			  i(action,name,photo)
                cm.listener = d	
		
class ChatNewHandler(BaseHandler, ChatMixin):
    @tornado.web.asynchronous
    def post(self): 
		chat = {}
		name = {}
		photo = {}
		action = []
		self.DB_NAME = self.get_argument("database")
		database = self.get_argument("database")
		cursor = self.get_globalid()
		rows = cursor.fetchall()
		for row in rows:
			self.chat_insert(row[0], self.get_argument("profileid"), self.get_argument("userid"), strip_tags(self.get_argument("message")), time.time())
			chat['actionid'] = row[0]
			chat['sentby'] = self.get_argument("profileid")
			chat['sentto'] = self.get_argument("userid")
			chat['message'] = strip_tags(self.get_argument("message"))
			chat['time'] = time.time();
			chat['type'] = 3
			name[chat['sentby']] = self.get_argument("name")
			photo[chat['sentby']] = self.get_argument("photo")
			action.append(chat)
			self.message(chat,name,photo,database)
			self.finish(dict(action=action,name=name,photo=photo))

class ChatUpdateHandler(BaseHandler, ChatMixin):
    @tornado.web.asynchronous
    def post(self):
		self.DB_NAME = self.get_argument("database")
		last_chat_time = self.get_argument("last_chat_time")
		user = self.get_argument("profileid")
		ack = 0
		name = {}
		photo = {}
		action = []
		if last_chat_time != '-1':
			cursor = self.chat_select(user, last_chat_time)
			rows = cursor.fetchall()
			for row in rows:
			   ack = 1	
			   chat = {}
			   chat['actionid'] = row[0]
			   chat['sentto'] = row[2]
			   chat['sentby'] = row[1]
			   chat['message'] = row[3]
			   print row[3]
			   chat['time'] = row[4]
			   chat['type'] = 3
			   name[int(row[1])] = self.get_name(row[1])
			   photo[int(row[1])] = self.get_photo(row[1])
			   action.append(chat)
		if ack == 1:		 
			self.retchat(action,name,photo)
			pass
		else:		
			self.wait(self.get_argument("database"), self.get_argument("profileid"), self.retchat)

    def retchat(self,action,name,photo):
        if self.request.connection.stream.closed():
            return	
        try :
		self.finish(dict(name=name,photo=photo,action=action))	
	except Exception,e:
   		print e 

class ChatTypingNewHandler(BaseHandler, ChatMixin):
	@tornado.web.asynchronous
	def post(self):
		chat = {}
		name = {}
		photo = {}
		self.DB_NAME = self.get_argument("database")
		chat['actionid'] = 0
		chat['sentby'] = self.get_argument("profileid")
		chat['sentto'] = self.get_argument("userid")
		chat['message'] = "" 
		chat['time'] = -1
		chat['type'] = 2
		name[int(chat['sentby'])] = self.get_argument("name")
		photo[int(chat['sentby'])] = ""
		self.typing(chat,name,photo,self.get_argument("database"))
		self.finish(dict(act=1))
		
class ChatSeenHandler(BaseHandler, ChatMixin):
	@tornado.web.asynchronous
	def post(self):
		chat = {}
		name = {}
		photo = {}
		self.DB_NAME = self.get_argument("database")
		chat['actionid'] = 0
		chat['sentby'] = self.get_argument("profileid")
		chat['sentto'] = self.get_argument("userid")
		chat['message'] = ""
		chat['time'] = -1
		chat['type'] = 1
		name[int(chat['sentby'])] = self.get_argument("name")
		photo[int(chat['sentby'])] = ""
		self.seen(chat,name,photo,self.get_argument("database"))
		self.chat_readbit_update(self.get_argument("profileid"), self.get_argument("userid"))
		self.finish(dict(act=1))			
		
class OnlineHandler(BaseHandler):
    online = {}
    identifier = []

    @tornado.web.asynchronous
    def post(self):
		self.DB_NAME = self.get_argument("database")
		self.online_user(self.get_argument("profileid"), self.retuser, self.get_argument("random"))

    def online_user(self, profileid, callback, random):
		cls = OnlineHandler
		self.online_replace(profileid, time.time())
		cls.online[callback] = profileid
		if random not in cls.identifier:                             # new user connected
		   cls.identifier.append(random)
		   for callback,u in cls.online.iteritems():
			   try:	
				  callback(u)
			   except:
				   pass
		   cls.online = {}
		else:
		   tornado.ioloop.IOLoop.instance().add_timeout(time.time()+30, lambda:callback(profileid,callback))

    def retuser(self, profileid, callback=None):
		name = {}
		photo = {}
		user = []
		if self.request.connection.stream.closed():
			return
		if callback:
			del OnlineHandler.online[callback]	
		cursor = self.online_select(profileid)
		rows = cursor.fetchall()
		ack = 0
		for row in rows:
		   user.append(row[0])	
		   name[int(row[0])] = self.get_name(row[0])
		   photo[int(row[0])] = self.get_photo(row[0])
		   ack = 1
		try:
		   self.finish(dict(name=name,photo=photo,user=user,ack=ack))
		except Exception,e:
		   print e 
		   
class OfflineHandler(tornado.web.RequestHandler, Query):
    def get(self):
		self.DB_NAME = self.get_argument("database")
		self.start_loop()

    def start_loop(self):
        tornado.ioloop.IOLoop.instance().add_timeout(time.time()+60, lambda:self.delete_user())

    def delete_user(self):
        self.offline_replace(time.time()-32.0)
        self.start_loop()		   
 
def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
