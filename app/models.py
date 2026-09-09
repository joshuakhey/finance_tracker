from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(255), unique=True, nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    merchant_name = db.Column(db.String(255), nullable=True)
    raw_name = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    date = db.Column(db.Date, nullable=False)
    pending = db.Column(db.Boolean, nullable=False, default=False)
    needs_categorization = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    account = db.relationship('Account', back_populates='transactions')
    category = db.relationship('Category', back_populates='transactions')


class Account(db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(255), unique=True, nullable=False)
    provider = db.Column(db.String(255), nullable=False)
    institution = db.Column(db.String(255), nullable=False)
    account_name = db.Column(db.String(255), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    is_investment = db.Column(db.Boolean, nullable=False, default=False)
    last_synced_at = db.Column(db.DateTime, nullable=True)
    account_category = db.Column(db.String(50), nullable=False, default='banking')

    transactions = db.relationship('Transaction', back_populates='account')
    account_balances = db.relationship('AccountBalance', back_populates='account')
    holdings = db.relationship('Holding', back_populates='account')
    sync_logs = db.relationship('SyncLog', back_populates='account')

class AccountBalance(db.Model):
    __tablename__ = 'account_balances'
    __table_args__ = (db.UniqueConstraint('account_id', 'date'),)

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    balance = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    date = db.Column(db.Date, nullable=False)

    account = db.relationship('Account', back_populates='account_balances')


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    icon = db.Column(db.String(255), nullable=True)
    is_system = db.Column(db.Boolean, default=False)

    transactions = db.relationship('Transaction', back_populates='category')
    merchant_rules = db.relationship('MerchantRule', back_populates='category')


class MerchantRule(db.Model):
    __tablename__ = 'merchant_rules'

    id = db.Column(db.Integer, primary_key=True)
    merchant_pattern = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)

    category = db.relationship('Category', back_populates='merchant_rules')


class Holding(db.Model):
    __tablename__ = 'holdings'

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Numeric(10, 4), nullable=False)
    average_price = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    market_price = db.Column(db.Numeric(10, 2), nullable=True)
    market_value = db.Column(db.Numeric(10, 2), nullable=True)

    account = db.relationship('Account', back_populates='holdings')


class SyncLog(db.Model):
    __tablename__ = 'sync_logs'

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    sync_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    account = db.relationship('Account', back_populates='sync_logs')