from flask import redirect, url_for, request, Blueprint, render_template
from ..models import db, Account, Transaction, Category
from sqlalchemy import func

from datetime import date

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/transactions', methods=['GET'])
def list_transactions():
    
    today = date.today()

    category_id = request.args.get('category_id')
    account_id = request.args.get('account_id', type=int)

    start = request.args.get('start', default=today.replace(day=1), type=lambda d: date.fromisoformat(d))
    end = request.args.get('end', default=today, type=lambda d: date.fromisoformat(d))

    query = Transaction.query
    query = query.filter(
        Transaction.date >= start,
        Transaction.date <= end
    )

    if category_id:
        query = query.filter(Transaction.category_id == category_id)

    if account_id:
        query = query.filter(Transaction.account_id == account_id)

    transactions = query.order_by(Transaction.date.desc()).all()
    
    return render_template('transactions.html', transactions=transactions)


@transactions_bp.route('/transactions/uncategorized', methods=['GET'])
def list_uncategorized_transactions():
    transactions = Transaction.query.filter(Transaction.category_id.is_(None)).order_by(Transaction.date.desc()).all()
    return render_template('uncategorized_transactions.html', transactions=transactions)


@transactions_bp.route('/transactions/<int:txn_id>/categorize', methods=['POST'])
def categorize(txn_id):
    transaction = Transaction.query.get_or_404(txn_id)
    category_id = request.form.get('category_id')
    transaction.category_id = category_id
    transaction.needs_categorization = False
    db.session.commit()
    return redirect(url_for('transactions.list_uncategorized_transactions'))