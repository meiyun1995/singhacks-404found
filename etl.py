import uuid
import pandas as pd

from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Boolean, DateTime, Integer, Date, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID


Base = declarative_base()


def parse_date(val):
    """Convert date strings to datetime or None."""
    if pd.isna(val):
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(str(val), fmt)
        except ValueError:
            continue
    return None


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_jurisdiction = Column(String(2), nullable=False)
    regulator = Column(String(10))
    booking_datetime = Column(String(20), nullable=False)
    value_date = Column(String(10))
    amount = Column(Float)
    currency = Column(String(3))
    channel = Column(String(10))
    product_type = Column(String(50))

    originator_name = Column(String(100))
    originator_account = Column(String(50))
    originator_country = Column(String(2))
    beneficiary_name = Column(String(100))
    beneficiary_account = Column(String(50))
    beneficiary_country = Column(String(2))

    swift_mt = Column(String(10), nullable=True)
    ordering_institution_bic = Column(String(10), nullable=True)
    beneficiary_institution_bic = Column(String(20), nullable=True)
    swift_f50_present = Column(Boolean, default=False)
    swift_f59_present = Column(Boolean, default=False)
    swift_f70_purpose = Column(String(255), nullable=True)
    swift_f71_charges = Column(String(3), nullable=True)

    travel_rule_complete = Column(Boolean, default=False)

    fx_indicator = Column(Boolean, default=False)
    fx_base_ccy = Column(String(3), nullable=True)
    fx_quote_ccy = Column(String(3), nullable=True)
    fx_applied_rate = Column(Float, default=0.0)
    fx_market_rate = Column(Float, default=0.0)
    fx_spread_bps = Column(Integer, default=0)
    fx_counterparty = Column(String(100), nullable=True)

    customer_id = Column(String(50), index=True)
    customer_type = Column(String(20))
    customer_risk_rating = Column(String(10))
    customer_is_pep = Column(Boolean, default=False)
    kyc_last_completed = Column(String(10))
    kyc_due_date = Column(String(10))
    edd_required = Column(Boolean, default=False)
    edd_performed = Column(Boolean, default=False)
    sow_documented = Column(Boolean, default=False)

    purpose_code = Column(String(3))
    narrative = Column(String(255))
    is_advised = Column(Boolean, default=False)
    product_complex = Column(Boolean, default=False)
    client_risk_profile = Column(String(10))
    suitability_assessed = Column(Boolean, default=False)
    suitability_result = Column(String(10))
    product_has_va_exposure = Column(Boolean, default=False)
    va_disclosure_provided = Column(Boolean, default=False)
    cash_id_verified = Column(Boolean, default=False)
    daily_cash_total_customer = Column(Float, default=0.0)
    daily_cash_txn_count = Column(Integer, default=0)

    sanctions_screening = Column(String(10))
    suspicion_determined_datetime = Column(String(20), nullable=True)
    str_filed_datetime = Column(String(20), nullable=True)

    # --- JSON serialization ---
    def to_dict(self):
        data = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)

            # Convert date strings to ISO
            if isinstance(value, str):
                # Try DD/MM/YYYY
                try:
                    value = datetime.strptime(value, "%d/%m/%Y").isoformat()
                
                except ValueError:
                    # Try SQLite default datetime with microseconds
                    try:
                        value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f").isoformat()
                    except ValueError:
                        pass
            data[column.name] = value
        return data

    def __repr__(self):
        return f"<Transaction(transaction_id={self.transaction_id}, amount={self.amount}, currency={self.currency})>"


if __name__ == "__main__":
    engine = create_engine("sqlite:///data/singhacks.db")
    Base.metadata.create_all(engine)

    transactions = pd.read_csv("data/transactions_mock_1000_for_participants.csv")
    transactions.to_sql("transactions", con = engine, if_exists = "replace", index = False, method = "multi")