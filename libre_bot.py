import libre_api
from manage import *
from medsenger_api import AgentApiClient
from helpers import *
from models import *

from rq import Queue
from libre_queue import conn
from libre_api import create_client

q = Queue('libre', connection=conn)
medsenger_api = AgentApiClient(API_KEY, MAIN_HOST, AGENT_ID, API_DEBUG)
browser = create_client()


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

    job = q.enqueue_call(
        func=libre_api.register_user, args=(contract, browser)
    )

    print(job.get_id())

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

    contract = Contract.query.filter_by(id=args.get('contract_id')).first()
    job = q.enqueue_call(
        func=libre_api.send_reports, args=([contract], browser)
    )

    print(job.get_id())

    return "Запущен процесс создания отчета, он придет в чат через минуту."


@app.route('/message', methods=['POST'])
@verify_json
def message(data):
    return "ok"

def sender(app):
    with app.app_context():
        job = q.enqueue_call(
            func=libre_api.send_reports, args=(Contract.query.all(), browser)
        )

        print("Full report job:", job.get_id())

if __name__ == "__main__":
    app.run(HOST, PORT, debug=API_DEBUG)
