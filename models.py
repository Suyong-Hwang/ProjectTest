import mysql.connector 
from datetime import datetime
from flask import session

class DBManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect(self): 
        try :
            self.connection = mysql.connector.connect(
                host = "10.0.66.5",
                user = "suyong",
                password="1234",
                database="test_db",
                charset="utf8mb4"
            )
            self.cursor = self.connection.cursor(dictionary=True)
        
        except mysql.connector.Error as error :
            print(f"데이터베이스 연결 실패 : {error}")
    
    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
    
    # 사용자 정보가져오기
    def get_user_by_id(self, userid):
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

    #테이블에 가입한 회원 데이터 삽입
    def register_pending_member(self, userid, username, password, birthday):
        sql = """
        INSERT INTO members (userid, username, password, birthday, status)
        VALUES (%s, %s, %s, %s, 'pending')
        """   
        try:
            self.connect()
            sql = """
                  INSERT INTO members (userid, username, password, birthday, status)
                  VALUES (%s, %s, %s, %s, 'pending')
                  """
            values = (userid, username, password, birthday)
            self.cursor.execute(sql, values)
            self.connection.commit()
            return True
        except Exception as error:
            print(f"회원 정보 저장 실패: {error}")
            return False
        finally:
            self.disconnect()

    #가입 승인 대기 유저 가져오기
    def get_pending_users(self):
        try:
            self.connect()
            sql = "SELECT * FROM members WHERE status = 'pending'"  # 승인 대기 중인 사용자들만 가져옵니다.
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as error:
            print(f"승인 대기 회원 정보 가져오기 실패 : {error}")
            return False
        finally:
            self.disconnect()