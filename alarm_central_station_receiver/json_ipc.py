"""
Copyright (2017) Chris Scuderi

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import socket
import json
import os

SOCKFILE = "/tmp/alarm_socket"


class ServerSock(object):
    def __init__(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def __enter__(self):
        self.sock.bind(SOCKFILE)
        self.sock.listen(5)

        return self.sock

    def __exit__(self, exc_type, exc_value, traceback):
        self.sock.close()
        os.remove(SOCKFILE)


def send_client_msg(request):
    try:
        serr = None
        rsp = None
        s = start_socket_client()
        send(s, request)
        rsp = recv(s)
        s.close()
    except socket.error as exc:
        serr = 'Exception: %s\nUnable to open socket, is alarmd running?' % exc

    return rsp, serr


def start_socket_client():
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect(SOCKFILE)
    return s


def send(sock, obj):
    msg = json.dumps(obj)
    packet = '%05d%s' % (len(msg), msg)
    sock.sendall(packet.encode())


def recv(sock):
    msg_len = sock.recv(5)
    msg = ''

    while len(msg) < int(msg_len):
        chunk = sock.recv(int(msg_len) - len(msg)).decode()
        assert chunk != ''
        msg = msg + chunk

    return json.loads(msg)
