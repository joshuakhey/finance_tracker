from flask import redirect, url_for, request, Blueprint, render_template, flash
from ..models import db, SyncLog, Account

sync_bp = Blueprint('sync', __name__)

@sync_bp.route('/sync', methods=['GET'])
def sync_status():
    query = SyncLog.query

    sync_logs = query.order_by(SyncLog.created_at.desc()).all()
    accounts = Account.query.all()
    
    return render_template('sync.html', sync_logs=sync_logs, accounts=accounts)


@sync_bp.route('/sync/run', methods=['POST'])
def call_sync():
    flash('Sync triggered successfully.', 'success')
    return redirect(url_for('sync.sync_status'))