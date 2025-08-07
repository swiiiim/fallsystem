from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# 사용자(TB_USER)
class User(UserMixin,db.Model):
    __tablename__ = 'tb_user'
    user_id = db.Column(db.String(50), primary_key=True)
    user_nm = db.Column(db.String(80), unique=True, nullable=False)
    user_pwd = db.Column(db.String(200), nullable=False)
    user_tel = db.Column(db.String(120), nullable=False)
    ins_dt = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    upt_dt = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def set_password(self, password):
        self.user_pwd = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.user_pwd, password)

    def get_id(self):
        return self.user_id

    def __repr__(self):
        return f'<User {self.user_id}>'

# 주문(TB_ORDER)
class OrderSave(db.Model):
   __tablename__ = 'tb_order'
   order_id = db.Column(db.String(255), primary_key=True)  # 주문 번호 (기본 키)
   customer_name = db.Column(db.String(255), nullable=False)  # 주문자 이름
   customer_phone = db.Column(db.String(15), nullable=False)  # 주문자 전화번호
   recipient_name = db.Column(db.String(255), nullable=False)  # 수령자 이름
   recipient_phone = db.Column(db.String(15), nullable=False)  # 수령자 전화번호
   recipient_postal_code = db.Column(db.String(10), nullable=False)  # 수령자 우편번호
   recipient_address_line1 = db.Column(db.String(255), nullable=False)  # 수령자 기본주소
   recipient_address_line2 = db.Column(db.String(255), nullable=True)  # 수령자 나머지 주소
   order_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())  # 주문일자
   product_name = db.Column(db.String(255), nullable=False)  # 제품명
   product_weight = db.Column(db.String(5), nullable=False)  # 중량
   product_quantity = db.Column(db.Integer, nullable=False)  # 수량
   delivery_message = db.Column(db.Text, nullable=True)  # 배송 메시지
   order_remark = db.Column(db.Text, nullable=True)  # 비고
   order_state = db.Column(db.String(15), nullable=False)  # 주문상태
   ins_dt = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
   upt_dt = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
   product_id = db.Column(db.String(11), nullable=False)  # 제품ID
   excel_date = db.Column(db.DateTime, nullable=False)  # 엑셀일자

def __repr__(self):
    return f'<Order {self.order_id}>'

# 제품(TB_PRODUCT)
class Product(db.Model):
    __tablename__ = 'tb_product'
    product_id = db.Column(db.String(10), primary_key=True)
    product_name = db.Column(db.String(255), unique=True, nullable=False)
    product_cd = db.Column(db.String(5), nullable=False)
    ins_dt = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    upt_dt = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f'<Product {self.product_id}>'

# 고객(TB_CUSTOMER)
class Customer(db.Model):
    __tablename__ = 'tb_customer'
    customer_id = db.Column(db.String(50), primary_key=True)
    customer_name = db.Column(db.String(100), unique=True, nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_post = db.Column(db.String(10), nullable=False)
    customer_address = db.Column(db.String(255), nullable=False)
    customer_address2 = db.Column(db.String(255), nullable=False)
    customer_remark = db.Column(db.String(500), nullable=False)
    ins_dt = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    upt_dt = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f'<Customer {self.product_id}>'


def generate_order_id():
    last_order = db.session.query(OrderSave).order_by(OrderSave.order_id.desc()).first()

    if last_order:
        last_id = last_order.order_id
        last_num = int(last_id[1:])
        new_num = last_num + 1
    else:
        new_num = 1  # 첫 번째 주문일 경우 F00001부터 시작

    new_id = f'F{new_num:05d}'
    return new_id

def generate_customer_id():
    last_customer = db.session.query(Customer).order_by(Customer.customer_id.desc()).first()

    if last_customer:
        last_id = last_customer.customer_id
        last_num = int(last_id[1:])
        new_num = last_num + 1
    else:
        new_num = 1  # 첫 번째 고객일 경우 C0000001부터 시작

    cust_new_id = f'C{new_num:07d}'
    return cust_new_id


def generate_finish_id():
    # 트랜잭션 락으로 가장 최근 finish_id 조회
    last_finish = db.session.query(Finish).with_for_update().order_by(Finish.finish_id.desc()).first()

    if last_finish and last_finish.finish_id.startswith("E"):
        next_id = int(last_finish.finish_id[1:]) + 1
        return f"E{str(next_id).zfill(5)}"
    else:
        return "E00001"

# 완료(tb_finish)
class Finish(db.Model):
   __tablename__ = 'tb_finish'
   finish_id = db.Column(db.String(255), primary_key=True)  # 완료 번호 (기본 키)
   customer_name = db.Column(db.String(255), nullable=False)  # 주문자 이름
   customer_phone = db.Column(db.String(15), nullable=False)  # 주문자 전화번호
   recipient_name = db.Column(db.String(255), nullable=False)  # 수령자 이름
   recipient_phone = db.Column(db.String(15), nullable=False)  # 수령자 전화번호
   recipient_postal_code = db.Column(db.String(10), nullable=False)  # 수령자 우편번호
   recipient_address_line1 = db.Column(db.String(255), nullable=False)  # 수령자 기본주소
   recipient_address_line2 = db.Column(db.String(255), nullable=True)  # 수령자 나머지 주소
   finish_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())  # 주문일자
   product_name = db.Column(db.String(255), nullable=False)  # 제품명
   product_weight = db.Column(db.String(5), nullable=False)  # 중량
   product_quantity = db.Column(db.Integer, nullable=False)  # 수량
   finish_remark = db.Column(db.Text, nullable=True)  # 비고
   finish_state = db.Column(db.String(15), nullable=False)  # 주문상태
   product_id = db.Column(db.String(11), nullable=False)  # 제품ID
   ins_dt = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
   upt_dt = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(),onupdate=db.func.current_timestamp())
   order_id = db.Column(db.String(255), nullable=False)  # 주문 번호

def __repr__(self):
    return f'<Order {self.finish_id}>'

class AlimtalkLog(db.Model):
    __tablename__ = 'alimtalk_logs'
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.String(50))
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    product_name = db.Column(db.String(255))
    sent_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())  # 보낸일자
    error_message = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f'<AlimtalkLog {self.log_id}>'
