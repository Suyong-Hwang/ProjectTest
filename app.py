from flask import Flask, session, url_for, render_template, flash, send_from_directory, jsonify ,request, redirect
import os
from datetime import datetime, timedelta
from functools import wraps
from models import DBManager

app = Flask(__name__)



app.secret_key = 'your-secret-key'  # 비밀 키 설정, 실제 애플리케이션에서는 더 안전한 방법으로 설정해야 함if __name__ == '__main__':

manager = DBManager()

##하루주기로 휴면 회원 자동 전환 

last_update= None
@app.before_request
def check_and_update_dormant_members():
    global last_update #외부에서 선언했기 떄문에 함수안에서 값을 변경하기위해서 global을 사용
    now = datetime.now()

    
    #처음 시작할 때 last_update가 None이면 현재 시간을 자정으로 설정
    if last_update is None:
        result = manager.update_dormant_members()
        if result:
            print("휴면 계정 업데이트 완료!")
        else:
            print("휴면 계정 업데이트 실패 또는 변경 없음.")
        last_update = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    
    # 하루가 경과하면 휴면 계정 업데이트 실행
    if (now - last_update).days >= 1:
        result = manager.update_dormant_members()
        if result:
            print("휴면 계정 업데이트 완료!")
        else:
            print("휴면 계정 업데이트 실패 또는 변경 없음.")

        # 다음 자정으로 last_update를 갱신
        last_update = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

### 푸터에 들어갈 날짜데이터 (context_processor 사용)
@app.context_processor
def inject_full_date():
    weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    today_date = datetime.now()
    today = today_date.strftime("%Y년 %m월 %d일")
    weekday = weekdays[today_date.weekday()]
    full_date = f"{today} ({weekday})"
    return {"full_date": full_date}

### 홈페이지
@app.route('/')
def index():
    return render_template('index.html')

### 로그인 기능
## 로그인 필수 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect('/login')  # 로그인되지 않았다면 로그인 페이지로 리디렉션
        return f(*args, **kwargs)
    return decorated_function

## 관리자 권한 필수 데코레이터
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session['role'] != 'admin':
            return "접근 권한이 없습니다", 403  # 관리자만 접근 가능
        return f(*args, **kwargs)
    return decorated_function


### 회원가입 페이지등록 
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        userid = request.form['userid']
        password = request.form['password']
        birthday = request.form['birthday']
        username = request.form['username']
        confirm_password = request.form['confirm_password']
        email = request.form['email']
        #암호가 일치하는지 확인
        if password != confirm_password:
            flash('암호가 일치하지 않습니다', 'error')
            return render_template('signup.html')
        #회원과 아이디가 중복되는지 확인
        if manager.duplicate_member(userid):
            flash('이미 존재하는 아이디 입니다.', 'error')
            return render_template('signup.html')
        #탈퇴 아이디와 중복확인
        if manager.duplicate_removed_member(userid):
            flash('이미 존재하는 아이디 입니다.','error')
            return render_template('signup.html')
        #회원가입 이메일 입력여부
        if not email:
            flash("이메일을 입력해주세요.", "danger")
            return render_template('signup.html')
        #회원 이메일과 중복여부
        if manager.duplicate_email(email):
            flash('이미 등록된 이메일 입니다.', 'error')
            return render_template('signup.html')
        #탈퇴 이메일과 중복여부 
        if manager.duplicate_removed_email(email):
            flash('이미 등록된 이메일 입니다.', 'error')
            return render_template('signup.html')
        # 생년월일이 올바른 날짜 형식인지 확인
        try:
            # 'YYYY-MM-DD' 형식으로 변환
            birthday = datetime.strptime(birthday, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            flash('잘못된 날짜 형식입니다. 생년월일을 다시 확인해주세요.', 'error')
            return render_template('signup.html')
        if manager.register_pending_member(userid, username, password, email, birthday):
            flash('회원가입 신청이 완료되었습니다. 관리자의 승인을 기다려 주세요.', 'success')
            return redirect(url_for('index'))
        flash('회원가입에 실패했습니다.', 'error')
        return redirect(url_for('register'))
    return render_template('signup.html')


## 로그인 정보 가져오기
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userid = request.form['userid']
        password = request.form['password']
        
        # 사용자 정보 확인
        user = manager.get_member_by_id(userid)  # DB에서 사용자 정보를 가져옴

        if user:  # user가 None이 아닐 경우에만 진행
            if userid and password:
                if user['status'] == 'approved':  # 승인된 사용자만 로그인 가능
                    if user['password'] == password:  # 아이디와 비밀번호가 일치하면
                        session['user'] = userid  # 세션에 사용자 아이디 저장
                        session['role'] = user['role']  # 세션에 역할(role) 저장
                        session['username'] = user['username']  # 세션에 이름(username) 저장
                        if session['role'] == 'admin':
                            manager.update_last_login(userid) #로그인 성공 후 마지막 로그인 갱신
                            return redirect(url_for('admin_dashboard'))  # 관리자는 관리자 대시보드로
                        elif session['role'] == 'dormant_member':
                            return redirect(url_for('dormant_member_dashboard'))
                        else:
                            manager.update_last_login(userid) #로그인 성공 후 마지막 로그인 갱신
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

## 로그아웃 라우트
@app.route('/logout')
def logout():
    # session.pop('user', None)  # 세션에서 사용자 정보 제거
    # session.pop('role', None)  # 세션에서 역할 정보 제거
    session.clear()
    return redirect('/')  # 로그아웃 후 로그인 페이지로 리디렉션

### 관리자 페이지
@app.route('/admin')
@admin_required  # 관리자만 접근 가능
def admin_dashboard():
    # 승인 대기 중인 사용자들 조회
    pending_count= manager.pending_member_count() #가입신청 회원 수
    activation_count = manager.activation_request_count() #휴면계정 활성화 신청 회원 수
    service_approval_count = manager.service_approval_count() #서비스 활성화 신청 회원 수


    # 가입 승인 대기 중인 사용자가 있으면 Flash 메시지 추가
    if pending_count >0: 
        flash(f'가입 승인 요청이 {pending_count}건 있습니다.', 'info')
    
    # 휴면계정 활성화 신청 회원이 있으면 Flash 메시지 추가
    if activation_count >0:
        flash(f'휴면계정 활성화 요청이 {activation_count}건 있습니다.', 'warning')

    if service_approval_count>0:
        flash(f'서비스 활성화 신청이 {service_approval_count}건 있습니다.','danger')

    return render_template('admin_dashboard.html')  # 관리자 대시보드 렌더링

###관리자 회원관리

##회원 목록 관리 페이지
@app.route('/admin/member_management')
@admin_required
def member_management():
    return render_template('member_management.html')

## 모든 회원 목록
@app.route('/admin/members')
@admin_required
def members():
    # 모든 회원 정보 조회
    number = manager.all_member_count()
    members = manager.get_all_members()
    return render_template('members.html', members=members, number = number )

## 서비스 이용 가능한 일반회원 목록
@app.route('/admin/can_service_members')
@admin_required
def can_service_members():
    number = manager.service_member_count()
    members = manager.get_members_with_service_permission()  # DB에서 일반회원 목록 불러오기
    return render_template('can_service_members.html', members=members, number=number)

## 서비스 이용 차단된 회원 목록
@app.route('/admin/denial_service_member')
@admin_required
def denial_service_member():
    number = manager.denied_member_count()
    members = manager.get_denied_service_members()  # DB에서 서비스 차단된 회원 목록 불러오기
    return render_template('denial_service_member.html', members=members, number=number)

## 회원 서비스 사용 권한
@app.route('/toggle_service_permission/<userid>', methods=['POST'])
@admin_required
def toggle_service_permission(userid):
    # 현재 상태를 반전시키기
    member = manager.get_member_by_id(userid)  # 현재 상태 가져오기
    if member:
        new_status = not member['can_service']  # 현재 상태의 반대로 설정
        if manager.update_service_permission(userid, new_status):  # DB 업데이트
            if new_status == 0:
                flash(f'{userid}님의 서비스사용 권한이 차단 되었습니다.', 'danger')
                return redirect(url_for('can_service_members'))
            else : 
                flash(f'{userid}님의 서비스사용 권한이 허용 되었습니다.', 'success')
                return redirect(url_for('denial_service_member'))
        else:
            flash(f'{userid}님의 서비스사용 권한 변경에 실패했습니다.', 'error')
    return redirect(url_for('member_management'))

## 가입 승인 대기중인 회원 목록
@app.route('/admin/pending_members')
@admin_required
def pending_members():
    number = manager.pending_member_count()
    members = manager.get_pending_members()  # DB에서 가입 대기중인 비회원 목록 불러오기
    return render_template('pending_members.html', members=members, number=number)

# 회원 상태 승인으로 변경
@app.route('/approve_user/<userid>', methods=['POST'])
@admin_required
def approve_user(userid):
    # 사용자의 status를 'approved'로 변경하고 role을 'can_service_memeber'로 설정
    if manager.approve_member(userid):
        flash(f'{userid} 회원의 승인 처리가 완료되었습니다.', 'success')
    else:
        flash(f'{userid} 회원 승인 처리에 실패했습니다.', 'error')
    return redirect(url_for('pending_members'))  # 회원 목록 페이지로 리디렉션


## 휴면 회원 목록
@app.route('/admin/dormant_members')
@admin_required
def dormant_members():
    number = manager.dormant_member_count() 
    dormant_members = manager.get_dormant_members()
    return render_template('dormant_members.html', dormant_members=dormant_members, number=number)

## 휴면 회원 활성화 하기
@app.route('/admin/members/activate/<userid>', methods=['POST'])
@admin_required
def activate_member(userid):
    # 해당 회원을 활성화하는 로직
    dormant_members = manager.get_dormant_members()  # 휴면 회원 정보를 가져오는 메서드 (예시)
    for member in dormant_members:
        if member :
            new_role = 'can_service_member'
            # 'role'을 'can_service_member'로 변경하고 'can_service'를 1로 설정
            manager.update_member_status(new_role, 1, userid)
            # 활성화 후 관리자 페이지로 리디렉션
            flash(f'{userid}님의 휴면 상태가 활성화로 업데이트 되었습니다.', 'success')
            return redirect(url_for('dormant_members'))
    else:
        # 잘못된 접근 시 리디렉션
        flash(f'{userid}님의 휴면 상태를 변경하지 못했습니다.', 'error')
        return redirect(url_for('dormant_members'))

##서비스 차단 회원 목록에서 강제탈퇴 누른 후 탈퇴진행
@app.route('/admin/remove_member/<userid>', methods=['GET','POST'])
@admin_required
def admin_remove_member(userid):
    # 
    if request.method == 'GET':
        return render_template('remove_member_dashboard.html', userid=userid)
    
    # POST 요청 시 회원 강제 탈퇴 처리
    if request.method == 'POST':
        member = manager.get_denied_service_member_by_id(userid)
        userid = member['userid']
        username = member['username']
        email = member['email']
        last_login = member['last_login'].strftime('%Y-%m-%d') if member['last_login'] else None
        #null값을 none으로 받아오기 때문에 none값을 기본값으로 설정해야함
        join_date = member['join_date'].strftime('%Y-%m-%d')
        birthday = member['birthday'].strftime('%y-%m-%d')
        reason = request.form['reason']  # 이유를 받아서 처리
        notes = request.form.get('notes', None)#추가 설명은 선택적 필드입니다.
        
        # 회원을 강제 탈퇴시키고, removed_members 테이블에 기록
        manager.add_removed_member(userid, username, email,last_login,join_date, birthday, removed_by='admin_initiated_deletion',reason=reason, notes=notes)
        manager.delete_member(userid)
        # 탈퇴 처리 후, 서비스 차단 목록 페이지로 리다이렉트
        return redirect(url_for('denial_service_member'))
    return redirect(url_for('denial_service_member'))

## 강제탈퇴된 회원 목록
@app.route('/admin/removed_members', methods=['GET'])
@admin_required
def removed_members():
    # DB에서 강제 탈퇴된 회원 정보를 가져옵니다
    members = manager.get_admin_removed_members()  # DB에서 정보를 가져오는 메서드
    # 강제 탈퇴된 회원 수를 구합니다
    number = len(members)
    # 페이지 렌더링 시 데이터 전달
    return render_template('admin_removed_members.html', members=members, number=number)

## 회원가입 거부 회원 테이블에서 삭제 후 데이터 romoved_members에 넣기
@app.route('/admin/reject_member/<userid>', methods=['GET','POST'])
@admin_required
def reject_member(userid):
    # 승인 거부 처리
    # 승인 거부 시 rejected_membership.html 페이지 가져옴
    if request.method == 'GET':
        return render_template('rejected_membership.html', userid=userid)
    
    #rejected_membership.html에서 승인거부시 데이터는 removed_members에 저장 후 members에서 삭제
    if request.method == 'POST':
        member = manager.get_pending_member_by_id(userid)  # 승인 대기 중인 회원 정보를 가져옴
        userid = member['userid']
        username = member['username']
        email = member['email']
        last_login = member['last_login'].strftime('%Y-%m-%d') if member['last_login'] else None
        join_date = member['join_date'].strftime('%Y-%m-%d')
        birthday = member['birthday'].strftime('%Y-%m-%d')
        reason = request.form['reason']  # 이유를 받아서 처리
        notes = request.form.get('notes', None)  # 추가 설명은 선택적 필드입니다.

        # 승인 거부 처리와 데이터 저장
        removed_by = 'rejected_membership'  # 승인 거부 사유
        manager.add_removed_member(userid, username, email, last_login, join_date, birthday, removed_by, reason, notes)
        manager.delete_member(userid)  # 회원 삭제

    # 승인 거부 처리 후, 대기 회원 목록 페이지로 리다이렉트
    return redirect(url_for('pending_members'))

#승인거부 비회원 목록 보기
@app.route('/admin/reject_member/rejected_members', methods=['GET'])
@admin_required
def rejected_members():
    # DB에서 강제 탈퇴된 회원 정보를 가져옵니다
    members = manager.get_admin_rejected_members()  # DB에서 정보를 가져오는 메서드
    # 강제 탈퇴된 회원 수를 구합니다
    number = len(members)
    # 페이지 렌더링 시 데이터 전달
    return render_template('admin_rejected_members.html', members=members, number=number)

#회원탈퇴 회원 목록 보기
@app.route('/admin/member_management/self_delete_member')
@admin_required
def admin_self_delete_members():
    members = manager.get_self_delete_members()
    if members is None:
        members = []

    number = len(members)
    return render_template('admin_self_delete_members.html', members=members, number=number)


### 회원 페이지
##로그인 후 회원페이지
@app.route('/dashboard')
@login_required  # 로그인된 사용자만 접근 가능
def dashboard():
    userid = session['user']
    member = manager.get_member_by_id(userid)
    return render_template('dashboard.html', member = member )


##로그인 후 휴면 회원일 경우 페이지
@app.route('/dormant_member_dashboard')
@login_required #로그인된 사용자만 접근 가능
def dormant_member_dashboard():
    userid = session['user']
    member = manager.get_dormant_by_id(userid)
    return render_template('dormant_member_dashboard.html', member = member)

#승인버튼 눌리면 관리자페이지에 표시
@app.route('/active_approve_request', methods=['GET','POST'])
@login_required
def active_approve_request():
    userid = session['user']
    result = manager.active_request_approval(userid)
    if result:
        flash("승인 요청이 완료되었습니다. 관리자의 승인을 기다려주세요.", "success")
    else:
        flash("승인 요청 중 오류가 발생했습니다. 다시 시도해주세요.", "error")
    return redirect(url_for('dormant_member_dashboard'))

#로그인 후 서비스 정지 회원이 서비스 정보 눌렀을때
@app.route('/denied_service_member_dashboard/<userid>', methods=['GET','POST'])
@login_required
def denied_service_member_dashboard(userid):
    if request.method == 'GET':
        return render_template('denied_service_member_dashboard.html',userid=userid)
    
    if request.method == 'POST':
        flash("서비스 활성화 신청이 접수되었습니다. 관리자 승인 대기 중입니다.", "success")
        return redirect(url_for('dashboard'))  

#승인버튼 눌리면 관리자페이지에 표시
@app.route('/service_approve_request', methods=['GET','POST'])
@login_required
def service_approve_request():
    userid = session['user']
    result = manager.service_request_approval(userid)
    if result:
        flash("승인 요청이 완료되었습니다. 관리자의 승인을 기다려주세요.", "success")
    else:
        flash("승인 요청 중 오류가 발생했습니다. 다시 시도해주세요.", "error")
    return redirect(url_for('dormant_member_dashboard'))

# 회원 탈퇴하기
@app.route('/self_delete_member/<userid>', methods=['GET','POST'])
@login_required
def self_delete_member(userid):
    #회원탈퇴 페이지 열기
    if request.method == 'GET':
        member = manager.get_member_by_info(userid)
        return render_template('self_delete_dashboard.html', member=member, userid=userid)  #회원 탈퇴페이지 열기
    #회원탈퇴 페이지에서 회원탈퇴버튼 눌러서 members에서 데이터 삭제 후 removed_members에 저장
    if request.method == 'POST':
        member = manager.get_member_by_info(userid) #로그인한 회원 정보 가져오기
        userid = member['userid']
        username = member['username']
        email = member['email']
        last_login = member['last_login'].strftime('%Y-%m-%d') if member['last_login'] else None
        join_date = member['join_date'].strftime('%Y-%m-%d')
        birthday = member['birthday'].strftime('%Y-%m-%d')
        reason = request.form['reason']  # 이유를 받아서 처리
        notes = request.form.get('notes', None)  # 추가 설명은 선택적 필드입니다.
        #회원탈퇴 데이터 저장
        removed_by = 'self_initiated_deletion'  # 승인 거부 사유
        manager.add_removed_member(userid, username, email, last_login, join_date, birthday, removed_by, reason, notes)
        manager.delete_member(userid)  # 회원 삭제

    #승인 거부 처리 후, 대기 회원 목록 페이지로 리다이렉트
    return render_template('complete_deletion.html', userid = userid)




#기능소개
@app.route('/feature')
def feature():
    return "기능 소개 페이지"

#문의하기 
@app.route('/enqire')
def enqire():
    return "문의하기"

#서비스시작
@app.route('/start_service')
def start_service():
    return "서비스 시작 페이지"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=True)