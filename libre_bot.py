import base64

from flask import jsonify

import libre_api
from manage import *
from medsenger_api import AgentApiClient
from helpers import *
from models import *
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

medsenger_api = AgentApiClient(API_KEY, MAIN_HOST, AGENT_ID, API_DEBUG)

sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[FlaskIntegration()],

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0
)



@app.route('/')
def index():
    return "Waiting for the thunder"


@app.route('/status', methods=['POST'])
@verify_json
def status(data):
    answer = {
        "is_tracking_data": True,
        "supported_scenarios": [],
        "tracked_contracts": [contract.id for contract in Contract.query.all()]
    }

    return jsonify(answer)


@app.route('/init', methods=['POST'])
@verify_json
def init(data):
    contract = Contract.query.filter_by(id=data.get('contract_id')).first()

    if not contract:
        contract = Contract(id=data.get('contract_id'))
        db.session.add(contract)

    info = medsenger_api.get_patient_info(data.get('contract_id'))
    # name=info.get('name'), birthday=info.get('birthday')

    contract.name = info.get('name')

    D, M, Y = info.get('birthday').split('.')
    M = M.replace('0', '')
    D = D.replace('0', '')
    contract.birthday = '/'.join((D, M, Y))
    contract.email = info.get('email')

    contract.yellow_top = float(data.get('params', {}).get('max_glukose', 13))
    contract.yellow_bottom = float(data.get('params', {}).get('min_glukose', 3.9))
    contract.red_top = 18
    contract.red_bottom = 3

    db.session.commit()

    contract = Contract.query.filter_by(id=data.get('contract_id')).first()

    T = threading.Thread(target=lambda:libre_api.register_user(contract))
    T.start()

    return "ok"


@app.route('/remove', methods=['POST'])
@verify_json
def remove(data):
    c = Contract.query.filter_by(id=data.get('contract_id')).first()
    if c:
        db.session.delete(c)
    return "ok"


# settings and views
@app.route('/settings', methods=['GET'])
@verify_args
def get_settings(args, form):
    return "Этот интеллектуальный агент не требует настройки."

@app.route('/report', methods=['GET'])
@verify_args
def get_report(args, form):
    contract = Contract.query.filter_by(id=args.get('contract_id')).first()


    T = threading.Thread(target=lambda:libre_api.send_reports([contract]))
    T.start()

    return "Запущен процесс создания отчет, он придет в чат через минуту."


@app.route('/message', methods=['POST'])
@verify_json
def message(data):
    return "ok"

def sender():
    with app.app_context():
        libre_api.send_reports(Contract.query.all())

if __name__ == "__main__":
    app.run(HOST, PORT, debug=API_DEBUG)
