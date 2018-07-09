"""
Copyright (2018) Chris Scuderi

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
import argparse
from flask import Flask, jsonify, request, abort, make_response
from alarm_central_station_receiver.json_ipc import send_client_msg

app = Flask(__name__)
debug_mode = False


@app.errorhandler(404)
def page_not_found_404(_):
    return jsonify(error='404 - not found'), 404


@app.errorhandler(500)
def page_not_found_500(_):
    return jsonify(error='500 - internal server error'), 500


def abort_json(message, code):
    abort(make_response(jsonify(error=message), code))


def send_request(req_msg):
    rsp, serr = send_client_msg(req_msg)
    if serr:
        abort_json(serr, 500)

    if rsp.get('error'):
        abort_json(rsp.get('error'), 422)

    return rsp.get('response')


@app.route("/api/alarm", methods=['GET'])
def get_alarm_status():
    return jsonify(send_request({'command': 'status'}))


@app.route("/api/alarm", methods=['PUT'])
def set_alarm_status():
    if request.json['arm_status'] not in ['arm', 'disarm']:
        abort_json('Invalid arm_status %s' % request.json['arm_status'], 422)

    send_request({'command': request.json['arm_status']})

    return get_alarm_status()


@app.route("/api/alarm/history", methods=['GET'])
def get_alarm_history():
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 10))
    if offset < 0 or limit < 0:
        abort_json('limit and offset must be > 0', 422)

    rsp = send_request({'command': 'history',
                        'options': {'start_idx': offset,
                                     'end_idx': offset + limit}
                        })

    return jsonify(history=rsp)


@app.before_request
def before():
    if debug_mode:
        print('===============================================')
        print('REQUEST')
        print(request.headers)
        print(request.get_data(as_text=True))
        print('===============================================')


@app.after_request
def after(response):
    if debug_mode:
        print('===============================================')
        print('RESPONSE')
        print(response.status)
        print(response.headers)
        print(response.get_data(as_text=True))
        print('===============================================')

    return response


def main():
    parser = argparse.ArgumentParser(
        prog='alarmd-webui',
        description='REST API WebUI for alarmd')

    parser.add_argument('--port',
                        type=int,
                        help='listen port')

    parser.add_argument('--host',
                        default='0.0.0.0',
                        help='listen hostname')

    parser.add_argument('--debug',
                        action='store_true',
                        default=False,
                        help='Debug mode')

    args = parser.parse_args()

    global debug_mode
    debug_mode = args.debug
    app.run(host=args.host, port=args.port, debug=debug_mode)
