from flask import Blueprint, render_template
from ..models import db, Account, Transaction, Category, AccountBalance, Holding
from sqlalchemy import func

from datetime import date



dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    today = date.today()
    month_start = today.replace(day=1)

    transactions = Transaction.query.filter(Transaction.date >= month_start).all()
    spend_sum = db.session.query(func.sum(Transaction.amount))\
        .filter(Transaction.amount > 0,
                Transaction.date >= month_start,
                Transaction.pending == False)\
        .scalar()    
    uncategorized_count = db.session.query(func.count(Transaction.id))\
        .filter(Transaction.amount > 0,
                Transaction.pending == False,
                Transaction.category_id.is_(None))\
        .scalar()
    recent_10_transactions = Transaction.query.order_by(Transaction.date.desc()).limit(10).all()


    account_balances = db.session.query(func.sum(AccountBalance.balance))\
        .join(Account)\
        .filter(Account.account_category == 'banking', AccountBalance.date == today)\
        .scalar()

    investment_balances = db.session.query(func.sum(Holding.market_value))\
        .join(Account)\
        .filter(Account.account_category == 'investment')\
        .scalar()

    net_worth = (account_balances or 0) + (investment_balances or 0)

    return render_template('dashboard.html', transactions=transactions, spend_sum=spend_sum, uncategorized_count=uncategorized_count, 
                            recent_10_transactions=recent_10_transactions, account_balances=account_balances, investment_balances=investment_balances, 
                            net_worth=net_worth)

