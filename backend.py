
import random
import string
import records
# from secrets import secrets as secrets
import logging
from logging import Logger
from handlers import LogHandler
import os
logger=Logger("BillTrakBackend")
logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

hdlr=LogHandler()
logger.addHandler(hdlr)
class BTBackend():
    
    try:
        db = records.Database(
            f"postgresql://192.168.5.172/billtrak?user=dj&password={os.getenv('dbpw')}")
    except Exception as e:
        logger.info("error in db connection {}".format(e))

    def genintid(self):
        return random.getrandbits(30)
        

    def gencharid(self):
        userid = ''.join(random.choices(
            string.ascii_letters + string.digits, k=8))
        return userid

    # def debugprint(self):
    #     rows=self.db.query("select * from bills")
    #     print(rows.all().paymenturl)
    #     pass
    def createuser(self,userid,password,email):
        query='''
        INSERT INTO users (userid, password,email) VALUES (
        :userid,
     crypt(:password, gen_salt('bf')),:email
            );
        '''
        try:
            
            self.db.query(query,userid=userid,password=password,email=email)
        except Exception as e:
            print("create user error {}".format(e))
    def createcompany(self, companyname, datecreated, userid,  category=None):
        companyid=self.genintid()
        query = "INSERT INTO company(companyid,companyname,datecreated,userid,category) VALUES(:companyid,:companyname,:datecreated,:userid,:category)"
        self.db.query(query, companyid=companyid, companyname=companyname,
                      datecreated=datecreated, category=category, userid=userid)
    def getbilldata(self,userid):
        # REMOVED FROM QUERY FOR TESTING
        # AND date_trunc('month', duedate) = date_trunc('month', current_date) 
        query="select * from billdatabyuserid WHERE userid=:userid order by duedate desc"
        rows = self.db.query(query,userid=userid)
        return rows.all()
    def getbillsbycompany(self, companyid,companyname):
        query = "select * from bills where companyid=:companyid"

        rows = self.db.query(query, companyid=self.getcompanyidbyname(companyname))
        return rows.all()

    def getbillinfo(self, billid,userid):
        query = "select * from billdatabyuserid WHERE billid=:billid and userid=:userid"

        rows = self.db.query(query, billid=billid,userid=userid).first()
        return rows

    def getcompanyidsbyuserid(self, userid):
        query = "select companyid from company where userid = :userid"
        return self.db.query(query, userid=userid).all()

    def getcompanycount(self,userid):
        query = "select companyname from company where userid = :userid"
        rows =self.db.query(query, userid=userid).all()
        return len(rows)

    def getcompanynames(self,userid):
        query = "select companyname from company where userid = :userid"
        rows =self.db.query(query, userid=userid).all()#exports rows to JSON for request from JS
        data=[]
        
        for row in rows:
            
            dat={"name":row.companyname
            }
            data.append(dat)
        return data

    def getbillrecurringstatus(self, billid):
        query = "select recurring from bills where billid=:billid"

        return self.db.query(query, billid=billid).first()
    def getemailbyuserid(self,userid):
        query="SELECT email from users where userid=:userid"
        return self.db.query(query, userid=userid).all()

    def validateuser(self, userid):
        pass
    def resetpw(self,newpassword,userid,oldpassword=None):
        query="""
        update users 
        set password = crypt(:newpassword, password)
        WHERE userid = :userid
        """
        try:
            self.db.query(query,newpassword=newpassword,userid=userid)
            return "SUCCESS"
        except:
            logger.error("Error running password reset query")
            return "FAILURE"
        
    def validatepw(self, password,userid):
        query="""
        SELECT *
        FROM users
        WHERE userid = :userid
        AND password = crypt(:password, password);
        """
        rows=self.db.query(query,password=password,userid=userid).all()
        print(len(rows)>0)
        return len(rows)>0
    def addmonthlyincome(self,userid,amt):
        query="""update users set monthlyincome=:amt where userid=:userid"""
        try:
            self.db.query(query,amt=amt,userid=userid)
        except Exception as e:
            print("error in add monthly income amount "+str(e))
    def getcompanyamts(self,userid):
        query="""
        select * from companyamts where userid =:userid
        """
        try:
            rows=self.db.query(query,userid=userid).all()
            return rows
        except Exception as e:
            print(e)
    def editbills(self,billid,amt,duedate,phonenum,paymenturl,confirmationnum):
        query="""UPDATE bills SET amt=:amt, duedate=:duedate,paymenturl=:paymenturl,phonenum=:phonenum, confirmationnum=:confirmationnum where billid=:billid """
        try:
            self.db.query(query,amt=amt,billid=billid,duedate=duedate,paymenturl=paymenturl,phonenum=phonenum,confirmationnum=confirmationnum)
        except Exception as e:
            logger.info(e)

    def updatebillamt(self,billid,amt):
        query="UPDATE bills SET amt=:amt,where billid=:billid "
        try:
            self.db.query(query,amt=amt,billid=billid)
        except:
            print("error in bill amt update")

    def updatebillrecurring(self, billid,recurring):
        query="update bills set recurring=:recurring where billid=:billid"
        
        self.db.query(query,billid=billid,recurring=not recurring)


    def deletebill(self, billid):
        query = "DELETE FROM bills WHERE billid=:billid"
        self.db.query(query, billid=billid)

    def getcompanyidbyname(self,companyname):
        query= "SELECT companyid from company where companyname=:companyname"
        rows =self.db.query(query,companyname=companyname).first()
        
        return rows.companyid
               
    def createbill(self,  billid, amt,  duedate, recurring,userid,companyname,confirmationnum,companyid=None,datepaid=None, paymenturl=None, phonenum=None, category=None):
        query = "INSERT INTO bills(billid,companyid,amt,datepaid,confirmationnum,paymenturl,category,phonenum,recurring,duedate) VALUES(:billid,:companyid,:amt,:datepaid,:confirmationnum,:paymenturl,:category,:phonenum,:recurring,:duedate)"
        
        companyid=self.getcompanyidbyname(companyname)
        self.db.query(query,  billid=billid, companyid=companyid, amt=amt, datepaid=datepaid, 
                      confirmationnum=confirmationnum, paymenturl=paymenturl,category=category, phonenum=phonenum,  recurring=recurring,duedate=duedate)

        
    def getnotifications(self):
        query=""" 
        select * from notificationall WHERE duedate > now() - interval '3 day'
        
        """
        rows=self.db.query(query).all()

        return rows

    

    def paybill(self,billid):
        query="""
        update bills set paid = not coalesce(paid, 'f') where billid=:billid
        
        
        """
        return self.db.query(query,billid=str(billid))