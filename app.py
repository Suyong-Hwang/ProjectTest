from flask import Flask, session, url_for, render_template, flash, send_from_directory, jsonify ,request, redirect
import os
from datetime import datetime
from functools import wraps
from models import DBManager
app = Flask(__name__)

app.secret_key = 'your-secret-key'  # 비밀 키 설정, 실제 애플리케이션에서는 더 안전한 방법으로 설정해야 함if __name__ == '__main__':

manager = DBManager()

# 로그인 필수 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect('/login')  # 로그인되지 않았다면 로그인 페이지로 리디렉션
        return f(*args, **kwargs)
    return decorated_function

# 관리자 권한 필수 데코레이터
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session['role'] != 'admin':
            return "접근 권한이 없습니다", 403  # 관리자만 접근 가능
        return f(*args, **kwargs)
    return decorated_function

# 로그인 정보 가져오기
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userid = request.form['userid']
        password = request.form['password']
        
        # 사용자 정보 확인
        user = manager.get_user_by_id(userid)  # DB에서 사용자 정보를 가져옴

        if user:  # user가 None이 아닐 경우에만 진행
            if userid and password:
                if user['status'] == 'approved':  # 승인된 사용자만 로그인 가능
                    if user['password'] == password:  # 아이디와 비밀번호가 일치하면
                        session['user'] = userid  # 세션에 사용자 아이디 저장
                        session['role'] = user['role']  # 세션에 역할(role) 저장
                        session['username'] = user['username']  # 세션에 이름(username) 저장
                        flash('로그인 성공!', 'success')
                        if session['role'] == 'admin':
                            return redirect(url_for('admin_dashboard'))  # 관리자는 관리자 대시보드로
                        else:
                            return redirect(url_for('dashboard'))  # 일반 사용자는 대시보드로
                    else:
                        flash('아이디 또는 비밀번호가 일치하지 않습니다.', 'error')  # 로그인 실패 시 메시지
                        return redirect(url_for('login'))  # 로그인 폼 다시 렌더링
                else:  # 승인되지 않은 사용자
                    flash('관리자의 가입승인이 필요합니다.', 'warning')  # 가입 승인 대기 중 메시지
                    return redirect(url_for('login'))  # 로그인 폼 다시 렌더링
            else:
                flash("아이디와 비밀번호를 모두 입력해 주세요.", 'error')
                return redirect(url_for('login'))  # 로그인 폼 다시 렌더링
        else:  # 존재하지 않는 사용자
            flash("존재하지 않는 아이디입니다.", 'error')
            return redirect(url_for('login'))  # 로그인 폼 다시 렌더링

    return render_template('login.html')  # GET 요청 시 로그인 폼 보여주기

# 회원가입 페이지등록 
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        userid = request.form['userid']
        password = request.form['password']
        birthday = request.form['birthday']
        username = request.form['username']
        confirm_password = request.form['confirm_password']
        #암호가 일치하는지 확인
        if password != confirm_password:
            flash('암호가 일치하지 않습니다', 'error')
            return render_template('signup.html')
        #아이디가 중복되는지 확인
        if manager.duplicate_member(userid):
            flash('이미 존재하는 아이디 입니다.', 'error')
            return render_template('signup.html')
        # 생년월일이 올바른 날짜 형식인지 확인
        try:
            # 'YYYY-MM-DD' 형식으로 변환
            birthday = datetime.strptime(birthday, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            flash('잘못된 날짜 형식입니다. 생년월일을 다시 확인해주세요.', 'error')
            return render_template('signup.html')
        if manager.register_pending_member(userid, username, password, birthday):
            flash('회원가입 신청이 완료되었습니다. 관리자의 승인을 기다려 주세요.', 'success')
            return redirect(url_for('index'))
        flash('회원가입에 실패했습니다.', 'error')
        return redirect(url_for('register'))
    return render_template('signup.html')

#홈페이지
@app.route('/')
def index():
    weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    today_date = datetime.now()
    today = today_date.strftime("%Y년 %m월 %d일")  # 날짜 포맷
    weekday = weekdays[today_date.weekday()]       # 요일 (0: 월요일, 6: 일요일)
    full_date = f"{today} ({weekday})"             # 날짜 + 요일 조합
    return render_template('index.html', full_date=full_date)

#기능소개
@app.route('/feature')
def feature():
    return "기능 소개 페이지"

#연락처 
@app.route('/contact')
def contact():
    return "연락처 페이지"

#서비스시작
@app.route('/start_service')
def start_service():
    return "서비스 시작 페이지"

#관리자 페이지
@app.route('/admin')
@admin_required  # 관리자만 접근 가능
def admin_dashboard():
    userid = session['user']
    user = manager.get_user_by_id(userid)

    # 승인 대기 중인 사용자들 조회
    pending_users = manager.get_pending_users()  # 'status'가 'pending'인 사용자들

    # 승인 대기 중인 사용자가 있으면 Flash 메시지 추가
    if pending_users:
        flash('가입 승인을 기다리는 유저가 있습니다.', 'warning')

    return render_template('admin_dashboard.html', user = user, pending_users=pending_users)  # 관리자 대시보드 렌더링



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=True)