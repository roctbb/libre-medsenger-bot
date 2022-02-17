import libre_api
from manage import *
from medsenger_api import AgentApiClient
from helpers import *
from models import *
from redis import Redis

medsenger_api = AgentApiClient(API_KEY, MAIN_HOST, AGENT_ID, API_DEBUG)
conn = Redis()


@app.route('/debug-sentry')
def trigger_error():
    division_by_zero = 1 / 0


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


def update_info(contract):
    info = medsenger_api.get_patient_info(contract.id)

    contract.name = info.get('name')

    D, M, Y = info.get('birthday').split('.')
    M = M.replace('0', '')
    D = D.replace('0', '')
    contract.birthday = '/'.join((D, M, Y))
    contract.email = info.get('email')


@app.route('/init', methods=['POST'])
@verify_json
def init(data):
    contract = Contract.query.filter_by(id=data.get('contract_id')).first()

    if not contract:
        contract = Contract(id=data.get('contract_id'))
        db.session.add(contract)

    update_info(contract)

    contract.yellow_top = float(data.get('params', {}).get('max_glukose', 13))
    contract.yellow_bottom = float(data.get('params', {}).get('min_glukose', 3.9))
    contract.red_top = 18
    contract.red_bottom = 3

    db.session.commit()

    contract = Contract.query.filter_by(id=data.get('contract_id')).first()

    cmd = {
        "cmd": "register",
        "id": contract.id
    }

    conn.publish('libre', json.dumps(cmd))

    print(f"Sent cmd: {cmd}")

    return "ok"


@app.route('/remove', methods=['POST'])
@verify_json
def remove(data):
    c = Contract.query.filter_by(id=data.get('contract_id')).first()
    if c:
        db.session.delete(c)
        db.session.commit()
    return "ok"


# settings and views
@app.route('/settings', methods=['GET'])
@verify_args
def get_settings(args, form):
    contract = Contract.query.filter_by(id=args.get('contract_id')).first()

    if not contract:
        abort(404)

    return render_template('settings.html', contract=contract)


@app.route('/settings', methods=['POST'])
@verify_args
def save_settings(args, form):
    contract = Contract.query.filter_by(id=args.get('contract_id')).first()

    if not contract:
        abort(404)

    try:
        contract.yellow_top = float(form['yellow_top'])
        contract.yellow_bottom = float(form['yellow_bottom'])
        contract.red_top = float(form['red_top'])
        contract.red_bottom = float(form['red_bottom'])
    except:
        return render_template('settings.html', contract=contract, error="Заполните все поля.")

    db.session.commit()

    return """<strong>Спасибо, окно можно закрыть</strong><script>window.parent.postMessage('close-modal-success','*');</script>"""


@app.route('/report', methods=['GET'])
@verify_args
def get_report(args, form):
    contract = Contract.query.filter_by(id=args.get('contract_id')).first()
    update_info(contract)
    db.session.commit()

    contract = int(args.get('contract_id'))

    cmd = {
        "cmd": "report",
        "ids": [contract]
    }

    conn.publish('libre', json.dumps(cmd))


    return "Запущен процесс создания отчета, он придет в чат через минуту."


@app.route('/message', methods=['POST'])
@verify_json
def message(data):
    return "ok"


def sender(app):
    with app.app_context():
        print("running sender...")

        ids = list(map(lambda x: x.id, Contract.query.all()))

        cmd = {
            "cmd": "report",
            "ids": ids
        }

        conn.publish('libre', json.dumps(cmd))

        print(f"Sent cmd: {cmd}")


if __name__ == "__main__":
    app.run(HOST, PORT, debug=API_DEBUG)
