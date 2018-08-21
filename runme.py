#!/bin/env python
import eventlet
eventlet.monkey_patch()

from app import create_app, socketio

app = create_app(debug=True)
socketio.init_app(app)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
