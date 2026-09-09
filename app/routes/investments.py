from flask import request, Blueprint, render_template
from ..models import db, Account, Holding
from sqlalchemy import func

investments_bp = Blueprint('investments', __name__)

@investments_bp.route('/investments', methods=['GET'])
def list_investments():
    
    account_id = request.args.get('account_id', type=int)

    query = Holding.query

    if account_id:
        query = query.filter(Holding.account_id == account_id)
    
    investments = query.order_by(Holding.market_value.desc()).all()
    q = db.session.query(func.sum(Holding.market_value))
    if account_id:
        q = q.filter(Holding.account_id == account_id)
    holdings_sum = q.scalar()

    cost_basis = db.session.query(func.sum(Holding.quantity * Holding.average_price))\
        .filter(Holding.account_id == account_id)\
        .scalar() if account_id else db.session.query(func.sum(Holding.quantity * Holding.average_price)).scalar()

    gain_loss = (holdings_sum or 0) - (cost_basis or 0)
    accounts = Account.query.filter_by(is_investment=True).all()

    return render_template('investments.html', investments=investments, holdings_sum=holdings_sum, cost_basis=cost_basis, 
                            gain_loss=gain_loss, accounts=accounts)