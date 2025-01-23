import mysql.connector 
from datetime import datetime
from flask import session

class DBManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    ## 데이터베이스 연결
    def connect(self): 
        try :
            self.connection = mysql.connector.connect(
                host = "10.0.66.6",
                user = "suyong",
                password="1234",
                database="test_db",
                charset="utf8mb4"
            )
            self.cursor = self.connection.cursor(dictionary=True)
        
        except mysql.connector.Error as error :
            print(f"데이터베이스 연결 실패 : {error}")
    
    ## 데이터베이스 연결해제
    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
    
    ## 선택한 회원 모든 정보 가져오기
    def get_member_by_info(self, userid):
        try:
            self.connect()
            sql = "SELECT * FROM members WHERE userid = %s"
            value = (userid,)
            self.cursor.execute(sql,value)
            return self.cursor.fetchone()
        except mysql.connector.Error as error :
            print(f"데이터베이스 연결 실패: {error}")
            return None 
        finally:
            self.disconnect()

    # 선택한 회원 아이디 가져오기
    def get_member_by_id(self, userid):
        try:
            self.connect()
            sql = "SELECT * FROM members WHERE userid = %s"
            value = (userid,)
            self.cursor.execute(sql,value)
            return self.cursor.fetchone()
        except mysql.connector.Error as error :
            print(f"데이터베이스 연결 실패: {error}")
            return None 
        finally:
            self.disconnect()
    

    ## 회원가입 유효성검사
    # 중복아이디 확인
    def duplicate_member(self, userid):
        try:
            self.connect()
            sql = 'SELECT * FROM members WHERE userid = %s'
            self.cursor.execute(sql, (userid,))
            result = self.cursor.fetchone()
            if result : 
                return True
            else :
                return False
        except mysql.connector.Error as error:
            self.connection.rollback()
            print(f"회원가입 실패: {error}")
            return False
        finally:
            self.disconnect()
    # 삭제된 아이디와 중복여부 확인
    def duplicate_removed_member(self, userid):
        try:
            self.connect()
            sql = 'SELECT * FROM removed_members WHERE userid = %s'
            self.cursor.execute(sql, (userid,))
            result = self.cursor.fetchone()
            if result : 
                return True
            else :
                return False
        except mysql.connector.Error as error:
            self.connection.rollback()
            print(f"회원가입 실패: {error}")
            return False
        finally:
            self.disconnect()

    # 이메일 중복 확인
    def duplicate_email(self, email):
        try:
            self.connect()
            sql = 'SELECT * FROM members WHERE email = %s'
            self.cursor.execute(sql, (email,))
            result = self.cursor.fetchone()
            if result : 
                return True
            else :
                return False
        except mysql.connector.Error as error:
            self.connection.rollback()
            print(f"회원가입 실패: {error}")
            return False
        finally:
            self.disconnect()
    
    #삭제된 회원중에서 이메일 중복 확인
    def duplicate_removed_email(self, email):
        try:
            self.connect()
            sql = 'SELECT * FROM removed_members WHERE email = %s'
            self.cursor.execute(sql, (email,))
            result = self.cursor.fetchone()
            if result : 
                return True
            else :
                return False
        except mysql.connector.Error as error:
            self.connection.rollback()
            print(f"회원가입 실패: {error}")
            return False
        finally:
            self.disconnect()

    ## 회원가입 정보 처리
    #테이블에 가입한 회원 데이터 삽입
    def register_pending_member(self, userid, username, password, birthday, email):
        try:
            self.connect()
            sql = """
                  INSERT INTO members (userid, username, password, birthday, email, status)
                  VALUES (%s, %s, %s, %s, %s, 'pending')
                  """
            values = (userid, username, password, email, birthday)
            self.cursor.execute(sql, values)
            self.connection.commit()
            return True
        except Exception as error:
            print(f"회원 정보 저장 실패: {error}")
            return False
        finally:
            self.disconnect()
    
    #전체 가입자 수 카운트 
    def all_member_count(self):
        try:
            # 회원 수 카운트 쿼리 실행
            sql = "SELECT COUNT(*) AS member_count FROM members WHERE role != 'admin'"
            self.connect()  # 데이터베이스 연결
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return result['member_count'] 
        except Exception as error:
            print(f"회원 수 조회 실패: {error}")
            return False
        finally:
            self.disconnect()
    
    #일반회원중 서비스 사용가능한 회원들 가져오기
    def get_members_with_service_permission(self):
        try:
            self.connect()
            sql = "SELECT * FROM members WHERE role = 'can_service_member'"
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as error:
            print(f"가입승인 회원 정보 가져오기 실패 : {error}")
            return False
        finally:
            self.disconnect()
    
    #일반회원중 서비스 사용가능한 회원들 수
    def service_member_count(self):
        try:
            # 회원 수 카운트 쿼리 실행
            sql = "SELECT COUNT(*) AS sevice_member_count FROM members WHERE role = 'can_service_member'"
            self.connect()  # 데이터베이스 연결
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return result['sevice_member_count'] 
        except Exception as error:
            print(f"회원 수 조회 실패: {error}")
            return False
        finally:
            self.disconnect()


    #일반회원중 서비스 사용불가 회원들 가져오기
    def get_denied_service_members(self):
        try:
            self.connect()
            sql = "SELECT * FROM members WHERE role = 'denial_service_member' "
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as error:
            print(f"서비스 사용 불가 회원들 정보 가져오기 실패 : {error}")
            return False
        finally:
            self.disconnect()
    
    #일반회원중 서비스 사용불가 회원 정보 가져오기
    def get_denied_service_member_by_id(self, userid):
        try:
            self.connect()
            sql = "SELECT * FROM members WHERE role = 'denial_service_member' and userid= %s"
            value=(userid,)
            self.cursor.execute(sql,value)
            return self.cursor.fetchone()
        except Exception as error:
            print(f"서비스 사용 불가 회원 정보 가져오기 실패 : {error}")
            return False
        finally:
            self.disconnect()

    #일반회원중 서비스 사용불가 회원수
    def denied_member_count(self):
        try:
            # 회원 수 카운트 쿼리 실행
            sql = "SELECT COUNT(*) AS denial_member_count FROM members WHERE role = 'denial_service_member'"
            self.connect()  # 데이터베이스 연결
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return result['denial_member_count'] 
        except Exception as error:
            print(f"회원 수 조회 실패: {error}")
            return False
        finally:
            self.disconnect()
    
    #가입 승인 대기 회원들 가져오기
    def get_pending_members(self):
        try:
            self.connect()
            sql = "SELECT * FROM members WHERE status = 'pending'"  # 승인 대기 중인 사용자들만 가져옵니다. 
            self.cursor.execute(sql,)
            return self.cursor.fetchall()
        except Exception as error:
            print(f"승인 대기 회원 정보 가져오기 실패 : {error}")
            return False
        finally:
            self.disconnect()

    #가입 승인 대기 회원 수 
    def pending_member_count(self):
        try:
            # 회원 수 카운트 쿼리 실행
            sql = "SELECT COUNT(*) AS pending_member_count FROM members WHERE role = 'non_member'"
            self.connect()  # 데이터베이스 연결
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return result['pending_member_count'] 
        except Exception as error:
            print(f"회원 수 조회 실패: {error}")
            return False
        finally:
            self.disconnect()

    #가입 승인 대기 회원 정보가져오기
    def get_pending_member_by_id(self,userid):
        try:
            self.connect()
            sql = "SELECT * FROM members WHERE userid = %s"  # 승인 대기 중인 사용자들만 가져옵니다.
            value = (userid,) 
            self.cursor.execute(sql,value)
            return self.cursor.fetchone()
        except Exception as error:
            print(f"승인 대기 회원 정보 가져오기 실패 : {error}")
            return False
        finally:
            self.disconnect()

    
    #일반회원들 가져오기
    def get_all_members(self):
        try:
            self.connect()
            sql = "SELECT * FROM members WHERE role != 'admin'"
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as error:
            print(f"가입승인 회원들 정보 가져오기 실패 : {error}")
            return False
        finally:
            self.disconnect()

    #사용권한 승인 업데이트
    def update_service_permission(self, userid, new_status):
        try:
            self.connect()
            # can_servie를 new_status로 업데이트하는 쿼리
            role = 'can_service_member' if new_status else 'denial_service_member' # role을 new_status 값에따라 변경
            sql = "UPDATE members SET can_service= %s, role = %s WHERE userid = %s"
            value = (new_status,role,userid)
            self.cursor.execute(sql, value)
            self.connection.commit()  # 커밋하여 변경 사항 저장
            return True
        except Exception as error:
            print(f"서비스사용 권한 변경 실패 : {error}")
            return False
        finally:
            self.disconnect()   
    
    # 회원 승인 업데이트
    def approve_member(self, userid):
        try:
            self.connect()
            # status를 'approved'로, role을 'user'로 업데이트하는 쿼리
            sql = "UPDATE members SET status = 'approved', role = 'can_service_member', can_service = 1 WHERE userid = %s"
            value = (userid, )
            self.cursor.execute(sql, value)
            self.connection.commit()  # 커밋하여 변경 사항 저장
            return True
        except Exception as error:
            print(f"회원 승인 처리 실패 : {error}")
            return False
        finally:
            self.disconnect()

    
    # 회원 마지막 로그인 시간 업데이트
    def update_last_login(self, userid):
        try:
            self.connect()
            sql = "UPDATE members SET last_login = CURDATE() WHERE userid = %s"
            self.cursor.execute(sql, (userid,))
            self.connection.commit()
        except Exception as error:
            print(f"로그인 시간 갱신 실패: {error}")
            raise
        finally:
            self.disconnect()

    ## 휴면 회원
    # 휴면회원으로 변경
    def update_dormant_members(self):
        try:
            self.connect()
            sql = """
            UPDATE members
            SET role = 'dormant_member', can_service = 0
            WHERE DATEDIFF(CURRENT_DATE, last_login) >= 90
            """
            self.cursor.execute(sql)
            self.connection.commit()
            return True
        except Exception as error:
            print(f"휴면 계정 업데이트 실패: {error}")
            return False
        finally:
            self.disconnect()
    
    ## 휴면회원 회원수
    def dormant_member_count(self):
        try:
            # 회원 수 카운트 쿼리 실행
            sql = "SELECT COUNT(*) AS dormant_member_count FROM members WHERE role = 'dormant_member'"
            self.connect()  # 데이터베이스 연결
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return result['dormant_member_count'] 
        except Exception as error:
            print(f"회원 수 조회 실패: {error}")
            return False
        finally:
            self.disconnect()

    ## 휴면회원들의 모든정보를 가져옴
    def get_dormant_members(self):
        try:
            self.connect()
            sql = "SELECT * FROM members WHERE role = 'dormant_member'"
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as error:
            print(f"휴면 회원들 조회 실패: {error}")
            return []
        finally:
            self.disconnect()

    ## 휴면회원 정보 가져오기
    def get_dormant_by_id(self, userid):
        try:
            self.connect()
            sql = "SELECT * FROM members WHERE role = 'dormant_member' and userid = %s"
            value = (userid,)
            self.cursor.execute(sql,value)
            return self.cursor.fetchall()
        except Exception as error:
            print(f"휴면 회원 정보 조회 실패: {error}")
            return []
        finally:
            self.disconnect()

    ## 휴면 계정 승인요청 
    def active_request_approval(self, userid):
        try:
            self.connect()
            sql = """
            UPDATE members
            SET active_approval_status = 'req
            uesting'
            WHERE userid = %s
            """
            self.cursor.execute(sql, (userid,))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"승인 요청 업데이트 실패: {e}")
            return False
        finally:
            self.disconnect()
    ##서비스 사용 불가 회원의 서비스 사용 승인 신청
    def service_request_approval(self, userid):
        try:
            self.connect()
            sql = """
            UPDATE members
            SET service_approval_status = 'requesting'
            WHERE userid = %s
            """
            self.cursor.execute(sql, (userid,))
            self.connection.commit()
            return True
        except Exception as error:
            print(f"승인 요청 업데이트 실패: {error}")
            return False
        finally:
            self.disconnect()

    ## 서비스 사용 승인 요청 인원
    def service_approval_count(self):
        try:
            # 서비스 활성화 요청 수 카운트 쿼리 실행
            sql = "SELECT COUNT(*) AS service_approval_count FROM members WHERE role = 'denial_service_member' AND service_approval_status = 'requesting'"
            self.connect()  # 데이터베이스 연결
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return result['service_approval_count']
        except Exception as error:
            print(f"휴면 계정 활성화 요청 수 조회 실패: {error}")
            return False
        finally:
            self.disconnect()

    ## 휴면 계정 회원 중 활성화 요청한 회원 수 조회
    def activation_request_count(self):
        try:
            # 휴면 계정 활성화 요청 수 카운트 쿼리 실행
            sql = "SELECT COUNT(*) AS activation_request_count FROM members WHERE role = 'dormant_member' AND active_approval_status = 'requesting'"
            self.connect()  # 데이터베이스 연결
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return result['activation_request_count']
        except Exception as error:
            print(f"휴면 계정 활성화 요청 수 조회 실패: {error}")
            return False
        finally:
            self.disconnect()
    
    ##휴면 회원 활성화 후 업데이트
    def update_member_status(self, new_role, new_can_service, userid):
        # SQL 쿼리로 해당 회원의 role과 can_service 값을 업데이트하는 예시
        try:
            self.connect()
            sql = """
            UPDATE members
            SET role = %s, can_service = %s, last_login=CURDATE(), approval_status=null
            WHERE userid = %s
            """
            values=(new_role,new_can_service,userid)
            self.cursor.execute(sql,values)
            self.connection.commit()
            return True
        except Exception as error:
            print(f"휴면 계정 업데이트 실패: {error}")
            return False
        finally:
            self.disconnect()
        
    ### 탈퇴 회원들 정보

    # 데이터베이스(members)에서 회원지우기
    def delete_member(self, userid):
        try:
            self.connect()
            sql = "DELETE FROM members WHERE userid = %s"
            value = (userid, )
            self.cursor.execute(sql,value)
            self.connection.commit()
            print(f'{userid}님의 회원 삭제가 완료되었습니다.')
            return True
        except Exception as error:
            print(f"회원 탈퇴 실패 : {error}")
            return False
        finally : 
            self.disconnect()

    ## 탈퇴 회원 정보 처리
    def add_removed_member(self, userid, username,email,last_login,join_date, birthday, removed_by, reason, notes=None):
        try:
            self.connect()
            sql = """
            INSERT INTO removed_members (userid, username, email, last_login,join_date, reason, removed_by, notes, birthday)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (userid, username, email,last_login,join_date, reason, removed_by, notes, birthday)
            self.cursor.execute(sql, values)
            self.connection.commit()
            print(f"{userid}님의 정보를 removed_members에 저장했습니다")
            return True
        except Exception as error:
            print(f"강제 탈퇴 정보 저장 실패: {error}")
            return False
        finally:
            self.disconnect()

    #강제탈퇴된 회원목록 가져오기
    def get_admin_removed_members(self):
        try:
            self.connect()
            sql = "SELECT * FROM removed_members WHERE removed_by = 'admin_initiated_deletion'"
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as error:
            print(f"강제 탈퇴된 회원 정보 가져오기 실패 : {error}")
            return False
        finally : 
            self.disconnect()

    #가입 승인 거부된 회원목록 가져오기
    def get_admin_rejected_members(self):
        try:
            self.connect()
            sql = "SELECT * FROM removed_members WHERE removed_by = 'rejected_membership'"
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as error:
            print(f"회원가입 거부된 비회원 정보 가져오기 실패 : {error}")
            return False
        finally : 
            self.disconnect()

    #회원 탈퇴 회원목록 가져오기
    def get_self_delete_members(self):
        try:
            self.connect()
            sql = "SELECT * FROM removed_members WHERE removed_by = 'self_inintiated_deletion'"
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as error:
            print(f"회원 탈퇴한 회원 정보 가져오기 실패 : {error}")
            return False
        finally : 
            self.disconnect()


    
    
    
    

    