"""Demo chat based on websockets."""

import itertools
import os.path
import time

from tinydb import TinyDB
import tornado.ioloop
import tornado.web
import tornado.websocket

DEBUG = True
DB_FILE = '/tmp/chat.db'
PORT = 8000
COOKIE_SECRET = 'secret'


database = TinyDB(DB_FILE)
colors = itertools.cycle(('#cc0', '#960', '#900', '#c03', '#300', '#906', '#939', '#306',
                          '#069', '#033', '#099', '#063', '#690', '#660', '#f00', '#f36',
                          '#93f', '#30f', '#399', '#696', '#996', '#666'))
page = os.path.join(os.path.dirname(__file__), 'chat.html')
page_html = open(page).read()


class ChatHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(page_html)


class ChatWebSocketHandler(tornado.websocket.WebSocketHandler):
    connections = set()

    def check_origin(self, origin):
        return True

    def open(self):
        user = "user-{:5}".format(str(time.time()).replace('.', '')[-11:])
        self.current_user = user
        self.color = next(colors)
        ChatWebSocketHandler.connections.add(self)
        self.write_message({'current_user': user, 'color': self.color})
        for message in database.all():
            self.write_message(message)

    def on_close(self):
        ChatWebSocketHandler.connections.remove(self)

    def on_message(self, message):
        message = message.strip()
        if message:
            data = {'user': self.current_user, 'message': message,
                    'color': self.color}
            database.insert(data)
            self.send_broadcast(data)

    def send_broadcast(self, data):
        for conn in self.connections:
            conn.write_message(data)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = (
            (r'/', ChatHandler),
            (r'/ws', ChatWebSocketHandler),)
        tornado.web.Application.__init__(self, handlers,
                                         cookie_secret=COOKIE_SECRET,
                                         debug=DEBUG)


def main():
    app = Application()
    app.listen(PORT)
    print("Starting chat server on http://127.0.0.1:{}/".format(PORT))
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
