import mysql.connector 
from datetime import datetime
from flask import jsonify
import json
import requests
import re

class DBManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    ## 데이터베이스 연결
    def connect(self): 
        try :
            self.connection = mysql.connector.connect(
                host = "10.0.66.10",
                user = "suyong",
                password="1234",
                database="test1_db",
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
    
    # 데이터 베이스에 회원 테이블 만들기
    def create_members_table(self):
        try:
            self.connect()
            sql = """
            CREATE TABLE IF NOT EXISTS members (
            `id` INT(11) NOT NULL AUTO_INCREMENT,
            `userid` VARCHAR(50) NOT NULL,
            `username` VARCHAR(100) NOT NULL,
            `password` VARCHAR(100) NOT NULL,
            `email` VARCHAR(100) NOT NULL,
            `birthday` DATE NOT NULL,
            `role` ENUM('can_service_member','denial_service_member','dormant_member','non_member','admin') DEFAULT 'non_member',
            `status` ENUM('approved','pending') DEFAULT 'pending',
            `can_service` TINYINT(1) DEFAULT 0,
            `last_login` DATE DEFAULT NULL,
            `active_approval_status` ENUM('requesting') DEFAULT NULL,
            `service_approval_status` ENUM('requesting') DEFAULT NULL,
            `join_date` DATE DEFAULT CURDATE(),
            `gender` VARCHAR(100) NOT NULL,
            PRIMARY KEY (`id`,`userid`,`email`)
            ) ENGINE=INNODB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
            """
            self.cursor.execute(sql)
            self.connection.commit()
            print("'members' 테이블이 성공적으로 생성되었습니다.")
        except mysql.connector.Error as error:
            print(f" 테이블 생성 실패: {error}")
        finally:
            self.disconnect()
    
    #회원 테이블에 관리자 계정 만들기
    def create_admin_user(self):
        try:
            self.connect()
            
            # admin 사용자가 있는지 확인
            check_sql = "SELECT COUNT(*) FROM members WHERE role = 'admin'"
            self.cursor.execute(check_sql)
            admin_count = self.cursor.fetchone()['COUNT(*)']
            
            if admin_count == 0:  # admin이 없으면
                # 관리자 데이터 추가
                sql = """
                INSERT INTO members (userid, username, password, email, birthday, role, status,can_service)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = ("hwang", "관리자", "1234", "hwang@example.com", "1989-10-01", "admin", "approved", 1)
                
                self.cursor.execute(sql, values)
                self.connection.commit()
                print("관리자 계정이 성공적으로 생성되었습니다.")
            else:
                print("이미 admin 계정이 존재합니다.")
        
        except mysql.connector.Error as error:
            print(f"관리자 계정 생성 실패: {error}")
        finally:
            self.disconnect()
    
    # 데이터 베이스에 회원탈퇴한 회원 테이블 만들기
    def create_removed_members_table(self):
        try:
            self.connect()
            sql = """
            CREATE TABLE IF NOT EXISTS removed_members (
            `userid` VARCHAR(100) NOT NULL,
            `username` VARCHAR(100) NOT NULL,
            `email` VARCHAR(255) NOT NULL,
            `last_login` DATE DEFAULT NULL,
            `join_date` DATE NOT NULL,
            `reason` VARCHAR(255) NOT NULL,
            `removed_by` VARCHAR(255) NOT NULL,
            `notes` TEXT DEFAULT NULL,
            `birthday` DATE NOT NULL,
            `removed_at` DATE DEFAULT NULL,
            PRIMARY KEY (`userid`,`email`),
            CONSTRAINT `CONSTRAINT_1` CHECK (`removed_by` IN ('admin_initiated_deletion','self_initiated_deletion','rejected_membership'))
            ) ENGINE=INNODB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
            """
            self.cursor.execute(sql)
            self.connection.commit()
            print("'removed_members' 테이블이 성공적으로 생성되었습니다.")
        except mysql.connector.Error as error:
            print(f" 테이블 생성 실패: {error}")
        finally:
            self.disconnect()

    # 데이터 베이스에 문의내용저장 테이블 만들기
    def create_enquiries_table(self):
        try:
            self.connect()
            sql = """
            CREATE TABLE IF NOT EXISTS enquiries (
            id INT(11) NOT NULL AUTO_INCREMENT,
            userid VARCHAR(50) DEFAULT NULL,
            username VARCHAR(100) DEFAULT NULL,
            email VARCHAR(255) NOT NULL,
            reason VARCHAR(255) NOT NULL,
            notes TEXT NOT NULL,
            enquired_at DATETIME DEFAULT CURRENT_TIMESTAMP(),
            answer_status VARCHAR(20) DEFAULT NULL,
            PRIMARY KEY (id)
            ) ENGINE=INNODB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
            """
            self.cursor.execute(sql)
            self.connection.commit()
            print("'enquiries' 테이블이 성공적으로 생성되었습니다.")
        except mysql.connector.Error as error:
            print(f" 테이블 생성 실패: {error}")
        finally:
            self.disconnect()

    #데이터 베이스에 기능성식품 테이블 만들기
    ## 건강기능식품 테이블 생성
    def create_raw_material_table(self):
        self.connect()  # DB 연결

        sql = """
        CREATE TABLE IF NOT EXISTS raw_material_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        raw_material_recognition_no VARCHAR(20) NOT NULL,  -- 원료인정번호
        daily_intake_upper_limit VARCHAR(50),  -- 1일 섭취량 상한선
        daily_intake_lower_limit VARCHAR(50),  -- 1일 섭취량 하한선
        weight_unit VARCHAR(20),  -- 중량 단위
        raw_material_name VARCHAR(255) NOT NULL,  -- 원재료 명
        cautionary_information TEXT,  -- 섭취 시 주의 사항 내용
        primary_functionality TEXT,  -- 주된 기능성
        edited_name VARCHAR(255),
        edited_functionality VARCHAR(255),
        file_name VARCHAR(255),
        link text
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        self.cursor.execute(sql)
        self.connection.commit()
        self.disconnect()  # DB 연결 해제
        print("raw_material_data 테이블 생성 완료")


    ## OpenAPI 데이터 저장
    def store_raw_material_data(self, api_url):
        response = requests.get(api_url)
        try:
            data = response.json()  
        except json.JSONDecodeError:
            print("JSON 변환 실패! response.text를 직접 파싱합니다.")
            data = json.loads(response.text)  

        try:
            raw_materials = data["I-0050"]["row"]
        except KeyError:
            print("API 응답 형식이 다릅니다. 'I-0050' 또는 'row' 키가 없습니다.")
            return

        if not isinstance(raw_materials, list):
            print("API 응답에서 'row' 데이터 형식이 리스트가 아닙니다.")
            return

        print(f"총 {len(raw_materials)}개의 데이터를 가져왔습니다.")

        self.connect()  

        sql = """
        INSERT INTO raw_material_data (
            raw_material_recognition_no, daily_intake_upper_limit, daily_intake_lower_limit, 
            weight_unit, raw_material_name, cautionary_information, primary_functionality
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            daily_intake_upper_limit = VALUES(daily_intake_upper_limit),
            daily_intake_lower_limit = VALUES(daily_intake_lower_limit),
            weight_unit = VALUES(weight_unit),
            raw_material_name = VALUES(raw_material_name),
            cautionary_information = VALUES(cautionary_information),
            primary_functionality = VALUES(primary_functionality);
        """

        for item in raw_materials:
            values = (
                item.get("HF_FNCLTY_MTRAL_RCOGN_NO"),
                item.get("DAY_INTK_HIGHLIMIT"),
                item.get("DAY_INTK_LOWLIMIT"),
                item.get("WT_UNIT"),
                item.get("RAWMTRL_NM"),
                item.get("IFTKN_ATNT_MATR_CN"),
                item.get("PRIMARY_FNCLTY")
            )
            self.cursor.execute(sql, values)

        self.connection.commit()
        self.disconnect()  
        print("✅ 중복 데이터는 업데이트하고, 새로운 데이터는 추가 완료!")

        

    # 선택한 회원 정보 가져오기
    def get_member_by_id(self, userid):
        try:
            self.connect()
            sql = "SELECT * FROM members WHERE userid = %s"
            value = (userid,)
            self.cursor.execute(sql,value)
            return self.cursor.fetchone()
        except mysql.connector.Error as error :
            print(f"회원정보 가져오기 연결 실패: {error}")
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
            return self.cursor.fetchone()    
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
    def register_pending_member(self, userid, username, password, birthday, email, gender):
        try:
            self.connect()
            sql = """
                  INSERT INTO members (userid, username, password, birthday, email, status, gender)
                  VALUES (%s, %s, %s, %s, %s, 'pending', %s)
                  """
            values = (userid, username, password, email, birthday, gender)
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
            value = (userid,)
            self.cursor.execute(sql, value)
            self.connection.commit()
        except Exception as error:
            print(f"로그인 시간 갱신 실패: {error}")
            raise
        finally:
            self.disconnect()

    ## 휴면 회원
    # 휴면회원으로 변경(현재날짜와 last_login 차이가 90일 이상이고, last_login=null이면 join_date로 대체)
    def update_dormant_members(self):
        try:
            self.connect()
            sql = """
            UPDATE members
            SET role = 'dormant_member'
            WHERE 
                (
                DATEDIFF(CURRENT_DATE, IFNULL(last_login, join_date)) >= 90
                )
                AND role != 'admin'
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
            return self.cursor.fetchone()
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
            SET active_approval_status = 'requesting'
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
            SET role = %s, can_service = %s, last_login=CURDATE(), active_approval_status=null
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
    def add_removed_member(self, userid, username, email, last_login, join_date, birthday, removed_by, reason, notes=None):
        try:
            self.connect()
            
            # removed_at에 CURDATE()를 명시적으로 설정
            sql = """
            INSERT INTO removed_members (userid, username, email, last_login, join_date, reason, removed_by, notes, birthday, removed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURDATE())
            """
            values = (userid, username, email, last_login, join_date, reason, removed_by, notes, birthday)
            
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
            sql = "SELECT * FROM removed_members WHERE removed_by = 'self_initiated_deletion'"
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as error:
            print(f"회원 탈퇴한 회원 정보 가져오기 실패 : {error}")
            return False
        finally : 
            self.disconnect()

    ## 홈페이지에서 문의한 내용 저장
    def add_enquire_index(self, email, reason, notes, filename):
        try:
            self.connect()
            # equires에 CURDATE()를 명시적으로 설정
            sql = """
            INSERT INTO enquiries (userid, username, email, reason, notes, enquired_at, filename)
            VALUES ('비회원', '비회원', %s, %s, %s, NOW(), %s)
            """
            values = (email,reason,notes, filename)
            self.cursor.execute(sql, values)
            self.connection.commit()
            print("문의 정보를 저장했습니다")
            return True
        except Exception as error:
            print(f"문의 정보를 저장 실패 : {error}")
            return False
        finally:
            self.disconnect()

    ## 로그인 후 문의한 내용 저장
    def add_enquire_member(self, userid, username, email, reason, notes, filename):
        try:
            self.connect()
            # equires에 CURDATE()를 명시적으로 설정
            sql = """
            INSERT INTO enquiries (userid, username, email, reason, notes, enquired_at, filename)
            VALUES (%s, %s, %s, %s, %s, NOW(), %s)
            """
            values = (userid,username,email,reason,notes, filename)
            self.cursor.execute(sql, values)
            self.connection.commit()
            print("문의 정보를 저장했습니다")
            return True
        except Exception as error:
            print(f"문의 정보를 저장 실패 : {error}")
            return False
        finally:
            self.disconnect()
    
    #회원 문의 정보 가져오기
    def get_enquired_posts_member(self):
        try:
            self.connect()
            sql="""
            SELECT * FROM enquiries WHERE userid != '비회원' 
            """
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as error:
            print(f"회원 문의 정보를 가져오기 실패 : {error}")
            return False
        finally:
            self.disconnect()
    
    #비회원 문의 정보 가져오기
    def get_enquired_posts_nonmember(self):
        try:
            self.connect()
            sql="""
            SELECT * FROM enquiries WHERE userid = '비회원' 
            """
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as error:
            print(f"회원 문의 정보들 가져오기 실패 : {error}")
            return False
        finally:
            self.disconnect()
    
    # 문의 상태 업데이트 메서드(같은아이디로 반복해서 문의가 올수 있으므로 아이디,작성시간으로 구분해서 처리)
    def update_answer_status(self, userid, enquired_at):
        try: 
            self.connect()
            sql = "UPDATE enquiries SET answer_status = 'completion' WHERE userid = %s and enquired_at = %s"
            value = (userid,enquired_at)
            self.cursor.execute(sql,value)
            self.connection.commit()
            print("답변상태를 업데이트 했습니다.")
            return True
        except Exception as error:
            print(f"답변상태를 업데이트하는데 실패했습니다. : {error}")
            return False
        finally:
            self.disconnect()
    
    # 문의한 회원 정보 가져오기
    def get_enquired_post_by_id(self, userid, enquired_at):
        try:
            self.connect()
            sql="""
            SELECT * FROM enquiries WHERE userid = %s and enquired_at=%s
            """
            value=(userid,enquired_at)
            self.cursor.execute(sql,value)
            return self.cursor.fetchone()
        except Exception as error:
            print(f"회원 문의 정보 가져오기 실패 : {error}")
            return False
        finally:
            self.disconnect()
    

    #서비스 사용 내역 데이터 테이블 만들기
    def create_service_usage_table(self):
        try:
            self.connect()
            # 테이블 생성 SQL 쿼리
            sql = """
            CREATE TABLE IF NOT EXISTS service_usage (
            id INT AUTO_INCREMENT PRIMARY KEY,
            userid VARCHAR(255) NOT NULL,
            username VARCHAR(255) NOT NULL,
            used_service_health_status TEXT NOT NULL,  -- 선택한 건강 상태 저장
            used_service_functionality TEXT NOT NULL, -- 선택한 기능성 저장
            used_service_at DATETIME NOT NULL -- 서비스 사용 시간 저장
            )ENGINE=INNODB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
            """
            # SQL 실행
            self.cursor.execute(sql)
            self.connection.commit()

            print("서비스 사용 내역 테이블이 성공적으로 생성되었습니다.")

        except Exception as error:
            print(f"테이블 생성 중 오류 발생: {error}")
        finally:
            self.disconnect()
    
    #서비스 사용내역 테이블에 데이터값 저장
    
    def save_service_usage(self, userid, username, health_status_str, functionality_choices_str):
        try:
            self.connect()  # DB 연결
            sql = """
            INSERT INTO service_usage (userid, username, used_service_health_status,used_service_functionality, used_service_at)
            VALUES (%s, %s, %s, %s, now())
            """
            values = (userid, username, health_status_str, functionality_choices_str)

            # SQL 실행
            self.cursor.execute(sql, values)
            self.connection.commit()
            print("서비스 사용 정보가 성공적으로 저장되었습니다.")
        except Exception as error:
            print(f"서비스 사용 정보 저장 중 오류 발생: {error}")
        finally:
            self.disconnect()  # DB 연결 종료

    #서비스 최근 사용내역 정보 가져오기
    def get_service_usage_by_userid(self, userid):
        try:
            self.connect()  # DB 연결
            sql = """
            SELECT * FROM service_usage 
            WHERE userid = %s 
            ORDER BY used_service_at DESC
            """
            value = (userid,)
            self.cursor.execute(sql, value)
            return self.cursor.fetchall()  # 모든 데이터 가져오기
        except Exception as error:
            print(f"서비스 이용 내역 조회 중 오류 발생: {error}")
            return []
        finally:
            self.disconnect() 
    
    # 회원 정보 변경
    def update_member_info(self, userid, username, email, birthday):
        try:
            self.connect()  # DB 연결
            sql= """
            UPDATE members
            SET username = %s, email = %s, birthday = %s
            WHERE userid = %s
            """
            values = (username, email, birthday, userid)
            self.cursor.execute(sql, values)
            self.connection.commit()  # 모든 데이터 가져오기
            print("회원정보가 수정되었습니다.")
            return True
        except Exception as error:
            print(f"회원정보 수정을 실패했습니다 : {error}")
            return False
        finally:
            self.disconnect() 
    
    # 회원 비밀번호 변경
    def update_password(self, userid, password):
        try:
            self.connect()  # DB 연결
            sql= """
                UPDATE members
                SET password = %s
                WHERE userid = %s
                """
            values = (password, userid)
            self.cursor.execute(sql, values)
            self.connection.commit()  # 모든 데이터 가져오기
            print("회원 비밀번호가 수정되었습니다.")
            return True
        except Exception as error:
            print(f"회원 비밀번호 수정을 실패했습니다 : {error}")
            return False
        finally:
            self.disconnect() 


    # 모든 제품 수 계산 함수
    def get_total_product_count(self):
        try:
            self.connect()
            sql = "SELECT COUNT(*) AS cnt FROM raw_material_data"
            self.cursor.execute(sql)
            print("제품 데이터 가져오기 성공")
            return self.cursor.fetchone()
        except Exception as error:
            print(f"전체 제품 수 가져오기 실패: {error}")
            return False
        finally:
            self.disconnect()

    # 모든 데이터의 페이지 네이션
    

    #모든 데이터의 페이지 네이션
    def get_all_products(self):
        try :
            self.connect()
            sql = """
                SELECT raw_material_name, daily_intake_upper_limit, 
                cautionary_information, primary_functionality 
                FROM raw_material_data
                """
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as error:
            print(f"모든제품 데이터가져오기 실패 : {error}")
            return False
        finally:
            self.disconnect()
    
    #제품이름 편집해서 저장
    def update_edited_product_data(self, products):
        try:
            self.connect()
            for product in products:
                raw_material_name = product['raw_material_name']
                # 모든 괄호와 그 안의 내용 제거
                product_name = re.sub(r'\(.*?\)', '', raw_material_name).strip()
                # 공백을 제거하여 하나의 단어로 결합
                product_name = product_name.replace(" ", "")  # 공백 제거

                # Process functionality
                if '(국문)' in product['primary_functionality']:
                    part_functionality = product['primary_functionality'].split('(국문)')[1].strip()
                else:
                    part_functionality = product['primary_functionality'].strip()
                if '(영문)' in part_functionality:
                    product_functionality = part_functionality.split('(영문)')[0].strip()
                else:
                    product_functionality = part_functionality
                edit_functionality = re.sub(r'\(기타[^\)]*\)', '', product_functionality ).strip()
                
                
                # Update the database with the edited name and functionality
                sql = """
                UPDATE raw_material_data
                SET edited_name = %s, edited_functionality = %s
                WHERE raw_material_name = %s
                """
                values = (product_name, edit_functionality, product['raw_material_name'])
                self.cursor.execute(sql, values)
                self.connection.commit()
            return True
    
        except Exception as error:
            print(f"편질할 데이터가 없거나 업데이트에 실패했습니다: {error}")
            return False
        finally :
            self.disconnect()

    #편집된 이름을 기준으로 중복없앤 데이터 가져오기
    def edit_product_data(self):
        try :
            self.connect()
            sql = """
                SELECT edited_name, cautionary_information, edited_functionality, daily_intake_upper_limit, link
                FROM raw_material_data 
                WHERE edited_name IS NOT NULL
                GROUP BY edited_name
                ORDER BY edited_functionality;
                """
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as error:
            print(f"모든제품 데이터가져오기 실패 : {error}")
            return False
        finally:
            self.disconnect()

    #편집된 이름을 기준으로 서비스로 추천된 데이터 가져오기
    def get_appropriate_products(self, health_status, functionality_choices):
        try:
            self.connect()
            sql = """
            SELECT edited_name, cautionary_information, edited_functionality, daily_intake_upper_limit, link
                FROM raw_material_data 
                WHERE edited_name IS NOT NULL
                GROUP BY edited_name
                ORDER BY edited_functionality;
            """
            self.cursor.execute(sql)
            products = self.cursor.fetchall()

            filtered_products = []

            # 2. 주의사항에서 건강상태 관련 경고 확인
            for product in products:
                # 건강 상태가 주의사항에 포함되어 있으면 제외
                if any(health_status_item in product['cautionary_information'] for health_status_item in health_status):
                    continue  # 건강 상태 리스트의 요소가 주의사항의 문자열에 포함되는 제품 제외
                
                # 3. 기능 체크박스 필터링
                if any(functionality_choices_item in product['edited_functionality'] for functionality_choices_item in functionality_choices):
                    filtered_products.append(product)
            return filtered_products
        
        except Exception as error:
            print(f"추천 제품 정보 가져오기 실패 : {error}")
            return False
        
        finally:
            self.disconnect()
    

    def update_file_name(self, edited_names):
        try:
            self.connect()
            for edited_name in edited_names:
                file_name = f"{edited_name}.png"
                sql = """
                    UPDATE raw_material_data
                    SET file_name = %s
                    WHERE edited_name = %s
                    """
                values = (file_name, edited_name)
                self.cursor.execute(sql, values)
                self.connection.commit()
            print(f"파일 이름 저장 성공")
            return True
        except Exception as error:
            print(f"파일 이름 저장 실패 : {error}")
            return False
        finally:
            self.disconnect()

       
        
          