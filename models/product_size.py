from . import db
from sqlalchemy import Sequence


class ProductSize(db.Model):
    __bind_key__ = 'db'
    id = db.Column(db.Integer, Sequence('ProductSize_sequence'), unique=True, nullable=False, primary_key=True)
    product_id = db.Column(db.Integer)
    size_label = db.Column(db.String(10))  # e.g., S, M, L, XL
    stock = db.Column(db.Integer, nullable=False)
