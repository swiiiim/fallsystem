import pandas as pd
from flask import Flask, Blueprint, request, redirect, url_for, render_template, session, send_file,jsonify
from flask_login import LoginManager, login_user, login_required, logout_user
from models import db, User, OrderSave, generate_order_id, Product, Customer,generate_customer_id,generate_finish_id, Finish
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
import xlsxwriter
from werkzeug.utils import secure_filename
import os
from dateutil import parser
from io import BytesIO
from sqlalchemy import text
from sqlalchemy import func

# 블루프린트 초기화
main = Blueprint('main', __name__, template_folder='KSY')

@main.route('/')
def home():
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # DB에서 사용자 검색
        user = User.query.filter_by(user_id=username).first()

        # 디버깅 출력
        if user:
            if user.check_password(password):
                login_user(user)
                session['user_id'] = user.user_id
                return redirect(url_for('main.home_page'))
            else:
                error = "비밀번호가 잘못되었습니다."
        else:
            error = "아이디가 잘못되었습니다."

    return render_template('login.html', error=error)


@main.route('/home')
@login_required
def home_page():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        return render_template('home.html', user=user)
    return redirect(url_for('main.login'))

@main.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)
    return redirect(url_for('main.login'))

@main.route('/save')
@login_required
def save():
    return render_template('save.html')

@main.route('/save', methods=['POST'])
def order_save():
    customer = Customer.query.filter_by(customer_name=request.form['customerName'],
                                        customer_phone=request.form['customerPhone']).first()
    if not customer:
        # 고객이 없으면 새로운 고객 레코드 추가
        new_customer_id = generate_customer_id()
        customername = request.form['recipientName']
        customerphone = request.form['recipientPhone']
        customer_post = request.form['zipCode']
        customer_address = request.form['address1']
        customer_address2 = request.form['address2']
        customer_remark = request.form.get('customerRemark', '')

        customer = Customer(
            customer_id=new_customer_id,
            customer_name=customername,
            customer_phone=customerphone,
            customer_post=customer_post,
            customer_address=customer_address,
            customer_address2=customer_address2,
            customer_remark=customer_remark
        )
        db.session.add(customer)

    new_order_id = generate_order_id()  # 새로운 주문 ID를 생성
    customername = request.form['customerName']
    customerphone = request.form['customerPhone']
    recipientname = request.form['recipientName']
    recipientphone = request.form['recipientPhone']
    zipcode = request.form['zipCode']
    address1 = request.form['address1']
    address2 = request.form['address2']
    remark = request.form['orderRemark']
    quantity = request.form['quantity']
    productname = request.form['productname']
    productid = request.form['productid']
    productweight = request.form['selectedProductCd']

    # 라디오 버튼 값 가져오기
    payment_status = request.form.get('payment_status', 'N')

    # 주문 상태 설정: 'N'이면 order_state = '1', 'Y'이면 order_state = '2'
    order_state = '2' if payment_status == 'Y' else '1'

    order = OrderSave(
        customer_name=customername,
        customer_phone=customerphone,
        recipient_name=recipientname,
        recipient_phone=recipientphone,
        recipient_postal_code=zipcode,
        recipient_address_line1=address1,
        recipient_address_line2=address2,
        order_date=db.func.current_timestamp(),  # 현재 시간 설정
        order_remark=remark,
        product_quantity=quantity,
        product_name=productname,
        product_id=productid,
        product_weight=productweight,
        order_id=new_order_id,
        order_state=order_state  # 라디오 버튼 값에 따라 설정
    )
    db.session.add(order)
    db.session.commit()

    # 주문 상태에 따른 메시지 설정
    status_message = "주문 완료 (입금완료)" if payment_status == 'Y' else "주문 완료 (미입금)"

    return status_message

#TB_PRODUCT 데이터 호출
@main.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    data = [
        {
            "product_id": product.product_id,
            "product_name": product.product_name,
            "product_cd": product.product_cd
        } for product in products
    ]
    return jsonify(data)

# 고객 팝업 사용 X
@main.route('/popcustomer')
@login_required
def popcustomer():
    return render_template('popcustomer.html')

#고객 전체 조회
@main.route('/search_customer/all', methods=['GET'])
def search_all_customers():
    all_customers = Customer.query.all()  # 전체 고객 조회
    customers = [{
        'customer_id': customer.customer_id,
        'customer_name': customer.customer_name,
        'customer_phone': customer.customer_phone,
        'customer_post': customer.customer_post,
        'customer_address': customer.customer_address,
        'customer_address2': customer.customer_address2,
        'customer_remark': customer.customer_remark,
        'ins_dt': customer.ins_dt,
        'upt_dt': customer.upt_dt
    } for customer in all_customers]

    return jsonify(customers)

#고객 조회
@main.route('/search_customer/<name>')
def search_customer(name):
    if name == 'null' or not name.strip():  # null이거나 비어있는 경우 전체 조회
        matched_customers = Customer.query.all()  # 전체 고객 조회
    else:
        matched_customers = Customer.query.filter(Customer.customer_name.contains(name)).all()  # 특정 이름인 경우 필터링

    customers = [{
        'customer_id': customer.customer_id,
        'customer_name': customer.customer_name,
        'customer_phone': customer.customer_phone,
        'customer_post': customer.customer_post,
        'customer_address': customer.customer_address,
        'customer_address2': customer.customer_address2,
        'customer_remark': customer.customer_remark,
        'ins_dt': customer.ins_dt,
        'upt_dt': customer.upt_dt
    } for customer in matched_customers]

    return jsonify(customers)

@main.route('/view')
@login_required
def view():
    return render_template('view.html')

@main.route('/fetch_orders', methods=['POST'])
@login_required
def fetch_orders():
    data = request.json
    query = db.session.query(OrderSave)

    # 기본 검색 조건
    order_states = data.get('order_state', '').split(',')
    if order_states:
        query = query.filter(OrderSave.order_state.in_(order_states))
    if 'name' in data and data['name']:
        query = query.filter(OrderSave.customer_name.contains(data['name']))
    if 'phone' in data and data['phone']:
        cleaned_phone = data['phone'].replace("-", "").replace(" ", "")
        query = query.filter(
            db.or_(
                db.func.replace(db.func.replace(OrderSave.customer_phone, "-", ""), " ", "").contains(cleaned_phone),
                db.func.replace(db.func.replace(OrderSave.recipient_phone, "-", ""), " ", "").contains(cleaned_phone)
            )
        )
    # **주문 날짜 최신순 정렬 (order_date 내림차순)**
    query = query.order_by(OrderSave.order_date.desc())
    orders = query.all()
    result = []
    for order in orders:
        try:
            #order_date = datetime.strptime(order.order_date, '%Y-%m-%d %H:%M')
            order_date = parser.isoparse(order.order_date)
        except ValueError:
            order_date = datetime.now()  # 변환 실패 시 현재 시간을 기본값으로 사용
        formatted_date = order_date.strftime('%Y-%m-%d %H:%M')

        result.append({
            'order_id': order.order_id,
            'order_state': order.order_state,  # order_state 추가
            'customer_name': order.customer_name,
            'customer_phone': order.customer_phone,
            'product_name': order.product_name,
            'product_quantity': order.product_quantity,
            'product_weight': order.product_weight,
            'recipient_name': order.recipient_name,
            'recipient_address_line1': order.recipient_address_line1,
            'recipient_address_line2': order.recipient_address_line2,
            'order_remark': order.order_remark,
            'recipient_phone': order.recipient_phone,
            'order_date': formatted_date,
            'product_id': order.product_id,
            'excel_date': order.excel_date
        })

    return jsonify(result)


# 주문 상태 업데이트 엔드포인트
@main.route('/cancel_order', methods=['POST'])
@login_required
def cancel_order():
    data = request.json
    order_id = data.get('order_id')
    new_state = data.get('order_state')

    if not order_id or not new_state:
        return jsonify({'success': False, 'error': '주문 ID와 상태를 확인하십시오.'}), 400

    try:
        order = db.session.query(OrderSave).filter_by(order_id=order_id).first()
        if not order:
            return jsonify({'success': False, 'error': '주문을 찾을 수 없습니다.'}), 404

        order.order_state = new_state
        order.excel_date = None  # Excel 날짜 필드를 NULL로 설정
        db.session.commit()

        return jsonify({'success': True})
    except SQLAlchemyError as e:
        print(f"Error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': '데이터베이스 오류가 발생했습니다.'}), 500


# 입금완료 업데이트
@main.route('/mark_as_paid', methods=['POST'])
@login_required
def mark_as_paid():
    data = request.json
    order_ids = data.get('order_ids', [])
    new_state = data.get('new_state')

    if not order_ids or new_state is None:
        return jsonify({'success': False, 'error': '주문 ID와 상태를 확인하세요.'}), 400

    try:
        orders = db.session.query(OrderSave).filter(OrderSave.order_id.in_(order_ids)).all()
        for order in orders:
            if order.order_state != '3':  # 이미 취소된 주문은 상태 변경 금지
                order.order_state = new_state

        db.session.commit()

        return jsonify({'success': True})
    except SQLAlchemyError as e:
        print(f"Error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': '데이터베이스 오류가 발생했습니다.'}), 500

# 엑셀업로드
ALLOWED_EXTENSIONS = {'xlsx'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@main.route('/download_excel')
def download_excel():
    # `order_state`가 '2'인 주문만 가져옵니다.
    orders = OrderSave.query.filter_by(order_state='2').all()
    data = []

    # 주문 데이터를 Excel에 맞는 형식으로 변환
    for order in orders:
        for _ in range(order.product_quantity):
            data.append({
                "주문자 이름": order.customer_name,
                "주문자 전화번호": order.customer_phone,
                "우편번호": "52510",
                "주소": "경남 사천시 축동면 탑리길 321-29(가을단감농원)",
                "수령자 이름": order.recipient_name,
                "수령자 우편번호": order.recipient_postal_code,
                "수령자 기본주소": order.recipient_address_line1 + " " + order.recipient_address_line2,
                "수령자 전화번호": order.recipient_phone,
                "배송 메시지": order.delivery_message,
                "중량": order.product_weight,
                "제품명": order.product_name,
                "수량": order.product_quantity,  # 수량 유지
            })

    # 데이터프레임 생성
    df = pd.DataFrame(data)

    # 엑셀 파일 생성
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Orders')

        # 열 너비를 자동 조정합니다.
        worksheet = writer.sheets['Orders']
        for idx, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2  # Padding 추가
            worksheet.set_column(idx, idx, max_len)

    output.seek(0)

    # 모든 `OrderSave` 레코드의 `excel_date`를 업데이트합니다.
    for order in orders:
        order.excel_date = datetime.utcnow()  # 현재 UTC 시간으로 설정

    db.session.commit()  # 업데이트된 `excel_date`를 데이터베이스에 저장

    # 오늘 날짜를 포함한 파일 이름 생성 (YYYY-MM-DD 형식)
    today_date = datetime.now().strftime("%Y-%m-%d")  # "YYYY-MM-DD" 형식으로 날짜 생성
    excelfile_name = f"{today_date}_가을단감농원(우체국).xls"

    # 엑셀 파일을 클라이언트에 다운로드로 제공
    return send_file(
        output,
        as_attachment=True,
        download_name= excelfile_name,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

#블루베리엑셀
@main.route('/download_blueexcel')
def download_blueexcel():
    # order_state가 '2'인 주문만 가져옵니다.
    orders = OrderSave.query.filter_by(order_state='2').all()
    data = []

    # 주문별로 1건씩만 기록하고, 수량/중량을 각각 주문 수량으로 기록
    for order in orders:
        data.append({
            "주문자 이름": order.customer_name,
            "주문자 전화번호": order.customer_phone,
            "우편번호": "52510",
            "주소": "경남 사천시 축동면 탑리길 321-29(가을단감농원)",
            "수령자 이름": order.recipient_name,
            "수령자 우편번호": order.recipient_postal_code,
            "수령자 기본주소": f"{order.recipient_address_line1} {order.recipient_address_line2}",
            "수령자 전화번호": order.recipient_phone,
            "배송 메시지": order.delivery_message,
            "중량": order.product_quantity,      # 중량도 수량과 동일하게
            "제품명": order.product_name,
            "수량": order.product_quantity,      # 주문 수량
        })

    # 데이터프레임 생성
    df = pd.DataFrame(data)

    # 엑셀 파일 생성
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Orders')

        # 열 너비 자동 조정
        worksheet = writer.sheets['Orders']
        for idx, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(idx, idx, max_len)

    output.seek(0)

    # excel_date 업데이트
    for order in orders:
        order.excel_date = datetime.utcnow()
    db.session.commit()

    # 파일 이름 생성
    today_date = datetime.now().strftime("%Y-%m-%d")
    excelfile_name = f"{today_date}_가을단감농원_블루베리(우체국).xls"

    return send_file(
        output,
        as_attachment=True,
        download_name=excelfile_name,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

#수정화면
@main.route('/update')
@login_required
def update():
    return render_template('update.html')


@main.route('/fetch_order_details', methods=['POST'])
def fetch_order_details():
    try:
        order_id = request.json.get('order_id')

        if not order_id:
            return jsonify({'error': 'Order ID is required'}), 400

        # 데이터베이스에서 주문 정보 검색
        order = OrderSave.query.filter_by(order_id=order_id).first()
        #order = OrderSave.query.get(order_id)

        if order:
            return jsonify({
                'order_id': order.order_id,
                'customer_name': order.customer_name,
                'customer_phone': order.customer_phone,
                'product_name': order.product_name,
                #'productSelect': order.product_name,
                'product_weight': order.product_weight,  # Decimal 타입을 문자열로 변환
                'product_quantity': order.product_quantity,
                'recipient_name': order.recipient_name,
                'recipient_phone': order.recipient_phone,
                'recipient_postal_code': order.recipient_postal_code,
                'recipient_address_line1': order.recipient_address_line1,
                'recipient_address_line2': order.recipient_address_line2,
                'order_remark': order.order_remark,
                'product_id': order.product_id,
                'order_state': order.order_state,



            })
        else:
            return jsonify({'error': 'Order not found'}), 404
    except Exception as e:
        app.logger.error(f"Error fetching order details: {e}")
        return jsonify({'error': 'An error occurred while fetching order details'}), 500


@main.route('/update', methods=['POST'])
def order_updatesave():
    try:
        order_id = request.form['orderid']
        order = OrderSave.query.filter_by(order_id=order_id).first()

        if not order:
            return jsonify({'error': 'Order not found'}), 404

        customer = Customer.query.filter_by(customer_name=request.form['customerName'],
                                            customer_phone=request.form['customerPhone']).first()

        if not customer:
            # 고객이 없으면 새로운 고객 레코드 추가
            new_customer_id = generate_customer_id()  # 커스터머 ID를 생성하는 함수
            customername = request.form['customerName']
            customerphone = request.form['customerPhone']
            customer_post = request.form['zipCode']
            customer_address = request.form['address1']
            customer_address2 = request.form['address2']
            customer_remark = request.form.get('customerRemark', '')

            customer = Customer(
                customer_id=new_customer_id,
                customer_name=customername,
                customer_phone=customerphone,
                customer_post=customer_post,
                customer_address=customer_address,
                customer_address2=customer_address2,
                customer_remark=customer_remark
            )
            db.session.add(customer)

        # 기존 주문을 업데이트합니다
        order.customer_name = request.form['customerName']
        order.customer_phone = request.form['customerPhone']
        order.recipient_name = request.form['recipientName']
        order.recipient_phone = request.form['recipientPhone']
        order.recipient_postal_code = request.form['zipCode']
        order.recipient_address_line1 = request.form['address1']
        order.recipient_address_line2 = request.form['address2']
        order.order_remark = request.form['orderRemark']
        order.product_quantity = request.form['quantity']
        order.product_name = request.form['productname']
        order.product_id = request.form['productid']
        order.product_weight = request.form['productweight']

        db.session.commit()

        return "수정 완료"
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saving order: {e}")
        return jsonify({'error': 'An error occurred while saving the order'}), 500


@main.route('/excelDate', methods=['POST'])
def order_exceldate():
    try:
        # 요청 데이터에서 order_id 추출
        order_id = request.form.get('orderid')  # get()을 사용하여 KeyError 방지
        if not order_id:
            return jsonify({'error': 'Order ID is required'}), 400

        # 데이터베이스에서 해당 주문 찾기
        order = OrderSave.query.filter_by(order_id=order_id).first()
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        # excel_date 컬럼 업데이트
        order.excel_date = db.func.current_timestamp()  # 쉼표 제거
        db.session.commit()  # 데이터베이스 트랜잭션 커밋

        return jsonify({'message': 'Excel date updated successfully'}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Database error: {e}")
        return jsonify({'error': 'An error occurred while updating the database'}), 500

    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@main.route('/excel')
@login_required
def excel():
    return render_template('excel_view.html')

@main.route('/finish')
@login_required
def finish():
    return render_template('finish.html')


def generate_finish_id():
    """
    PostgreSQL SEQUENCE를 통해 고유하고 순차적인 finish_id를 생성합니다.
    """
    # SEQUENCE에서 다음 고유 ID 값을 가져오기
    result = db.session.execute(text("SELECT nextval('tb_finish_id_seq')"))
    sequence_id = result.scalar()  # nextval() 값 반환
    return f"E{str(sequence_id).zfill(5)}"  # E00001 형식 반환


@main.route('/finishsave', methods=['POST'])
def finishsave():
    """선택된 order_id 데이터를 기반으로 tb_order에서 조회하여 tb_finish로 저장 및 상태 업데이트"""
    try:
        # 요청 데이터에서 선택된 order_id 리스트 가져오기
        order_ids = request.json.get('order_ids', [])

        if not order_ids or not isinstance(order_ids, list):
            return jsonify({'success': False, 'error': '유효한 order_id 리스트가 필요합니다.'}), 400

        new_records = []  # tb_finish에 추가할 레코드 목록
        skipped_ids = []  # 스킵된 order_id 목록

        for order_id in order_ids:
            # tb_order에서 order_id로 데이터 조회
            order_data = OrderSave.query.filter_by(order_id=order_id).first()

            if not order_data:
                skipped_ids.append(order_id)  # 없는 데이터는 스킵
                continue

            # `excel_date`가 NULL일 경우 스킵
            if not order_data.excel_date:
                skipped_ids.append(order_id)
                continue

            # 고유 finish_id 생성
            new_finish_id = generate_finish_id()

            # tb_finish에 저장할 새 레코드 생성
            new_finish_record = Finish(
                customer_name=order_data.customer_name,
                customer_phone=order_data.customer_phone,
                recipient_name=order_data.recipient_name,
                recipient_phone=order_data.recipient_phone,
                recipient_postal_code=order_data.recipient_postal_code,
                recipient_address_line1=order_data.recipient_address_line1,
                recipient_address_line2=order_data.recipient_address_line2,
                finish_remark=order_data.order_remark,
                product_quantity=order_data.product_quantity,
                product_name=order_data.product_name,
                product_id=order_data.product_id,
                product_weight=order_data.product_weight,
                finish_id=new_finish_id,
                finish_state='4',
                finish_date=db.func.current_timestamp(),
                order_id=order_data.order_id,
            )

            # tb_order의 상태 업데이트
            order_data.order_state = '4'

            # 새 레코드를 추가할 리스트에 저장
            new_records.append(new_finish_record)

        # tb_finish에 데이터 저장 및 tb_order 상태 업데이트
        if new_records:
            db.session.add_all(new_records)  # 새로운 Finish 레코드 삽입
            db.session.commit()  # 트랜잭션 커밋

        total_success = len(new_records)  # 성공적으로 처리된 주문 수
        total_skipped = len(skipped_ids)  # 처리되지 않은 주문 수

        return jsonify({
            'success': True,
            'message': f'{total_success}개의 주문이 성공적으로 저장되었습니다.',
            'skipped_ids': skipped_ids
        })

    except SQLAlchemyError as e:
        db.session.rollback()  # 트랜잭션 롤백
        print(f"Database Error: {e}")
        return jsonify({'success': False, 'error': '데이터베이스 오류가 발생했습니다.'}), 500

    except Exception as e:
        print(f"Unexpected Error: {e}")
        return jsonify({'success': False, 'error': '서버에서 예기치 않은 문제가 발생했습니다.'}), 500


@main.route('/fetch_finish', methods=['POST'])
def fetch_finish():
    """tb_finish와 tb_order의 상태가 '4'인 항목만 조회"""
    try:
        # 요청으로부터 필터를 받아올 수 있도록 처리 (옵션)
        filters = request.json or {}

        # 기본 필터 조건
        customer_name = filters.get('customer_name', None)
        customer_phone = filters.get('customer_phone', None)

        # Query 생성
        query = db.session.query(Finish).join(OrderSave, Finish.product_id == OrderSave.product_id) \
            .filter(Finish.finish_state == '4', OrderSave.order_state == '4')

        # 필터 조건 추가 (검색 옵션)
        if customer_name:
            query = query.filter(Finish.customer_name.like(f"%{customer_name}%"))
        if customer_phone:
            query = query.filter(Finish.customer_phone.like(f"%{customer_phone}%"))

        # 결과 조회
        results = query.all()

        # 결과를 JSON 형식으로 직렬화
        finish_list = [
            {
                "finish_id": row.finish_id,
                "customer_name": row.customer_name,
                "customer_phone": row.customer_phone,
                "recipient_name": row.recipient_name,
                "recipient_phone": row.recipient_phone,
                "recipient_postal_code": row.recipient_postal_code,
                "recipient_address_line1": row.recipient_address_line1,
                "recipient_address_line2": row.recipient_address_line2,
                "finish_date": row.finish_date.strftime('%Y-%m-%d %H:%M:%S'),
                "product_name": row.product_name,
                "product_weight": row.product_weight,
                "product_quantity": row.product_quantity,
                "finish_remark": row.finish_remark,
                "product_id": row.product_id
            } for row in results
        ]

        # JSON 응답 반환
        return jsonify({"success": True, "data": finish_list})

    except Exception as e:
        print(f"Error during fetching finish data: {e}")
        return jsonify({"success": False, "error": "서버에서 데이터를 조회하는 중 문제가 발생했습니다."}), 500


@main.route('/ordersum', methods=['GET'])
def order_sum():
    # 문자열 '2'로 비교
    filtered_orders = OrderSave.query.filter(OrderSave.order_state == '2')

    # 제품별 수량 및 중량 합계, 중량 오름차순 정렬
    grouped_data = (
        filtered_orders
        .with_entities(
            OrderSave.product_id,
            OrderSave.product_name,
            OrderSave.product_weight,
            func.sum(OrderSave.product_quantity).label('total_quantity')
        )
        .group_by(OrderSave.product_id, OrderSave.product_name, OrderSave.product_weight)
        .order_by(OrderSave.product_weight.asc())  # 중량 기준 오름차순 정렬
        .all()
    )

    order_sums = [{
        'product_id': item.product_id,
        'product_name': item.product_name,
        'product_weight': item.product_weight,
        'product_quantity': item.total_quantity,
    } for item in grouped_data]

    total_sum = sum(item['product_quantity'] for item in order_sums)

    return jsonify({
        'order_sums': order_sums,
        'total_quantity': total_sum
    })

# 애플리케이션 팩토리 함수 필수###############################################################
def create_app():
    app = Flask(__name__)
    # Secret Key 설정
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://KSY:1234@localhost/fallsystem'
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://KSY:1234@swiiiim-4559.postgres.pythonanywhere-services.com:14559/fallsystem'
    #소스 반영 할땐 이걸로 해야해 명심 하기
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 파일 업로드 제한

    db.init_app(app)



    # Flask-Login 설정
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'





    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    # 블루프린트 등록
    app.register_blueprint(main)

    return app

# 애플리케이션 생성
app = create_app()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
###########################################################################################
