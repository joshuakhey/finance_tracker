from flask import redirect, url_for, request, Blueprint, render_template, flash
from ..models import db, SyncLog, Account
from ..services.snaptrade_client import holdings_sync

sync_bp = Blueprint('sync', __name__)

@sync_bp.route('/sync', methods=['GET'])
def sync_status():
    query = SyncLog.query

    sync_logs = query.order_by(SyncLog.created_at.desc()).all()
    accounts = Account.query.all()
    
    return render_template('sync.html', sync_logs=sync_logs, accounts=accounts)

def save_sync_log(sync_type, account_id, status, message):
    sync_log = SyncLog(sync_type=sync_type, account_id=account_id, status=status, message=message)
    db.session.add(sync_log)
    db.session.commit()


@sync_bp.route('/sync/run', methods=['POST'])
def call_sync():
    try:
        result = holdings_sync()
        save_sync_log('holdings', None, 'success', 'Sync triggered successfully.')
        flash('Sync triggered successfully.', 'success')
    except Exception as e:
        save_sync_log('holdings', None, 'failure', str(e))
        flash(f'Sync failed: {str(e)}', 'danger')
        
    return redirect(url_for('sync.sync_status'))