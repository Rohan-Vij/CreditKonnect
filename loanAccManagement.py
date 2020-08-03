# flask import
from flask import Flask, render_template, request, session, Blueprint
# mongodb import
from pymongo import MongoClient
# packages for email sending
from itsdangerous import URLSafeTimedSerializer
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random

# MongoDB Cloud Database connection (using Azure server)
client = MongoClient(
    'mongodb+srv://mainUser:mainUserPass@fastapproval.f06cc.azure.mongodb.net/fastapproval?retryWrites=false&w=majority')
db = client["fastapproval"]
# Email sending initializing
verificationKey = URLSafeTimedSerializer('Thisisasecret!')

homePageBlue = Blueprint('homePage', __name__, template_folder='templates')
signupBlue = Blueprint('signup', __name__, template_folder='templates')
signoutBlue = Blueprint('signout', __name__, template_folder='templates')
loginBlue = Blueprint('login', __name__, template_folder='templates')
confirmEmailBlue = Blueprint('confirmEmail', __name__, template_folder='templates')
searchBlue = Blueprint('search', __name__, template_folder='templates')
sendToBankBlue = Blueprint('sendToBank', __name__, template_folder='templates')
checkBlue = Blueprint('check', __name__, template_folder='templates')

@homePageBlue.route("/")
def homepage():
    return render_template("loanUser/landing_page.html")

@checkBlue.route("/check", methods=["GET", "POST"])
def check():
    db.bankResponses.find({})

@signupBlue.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        fName = request.form['fname']
        lName = request.form['lname']
        usernameUp = request.form['user']
        passwordUp = request.form['pass']
        query = {"username": usernameUp}
        # Checking if the chosen username exists
        if db.loanUsers.find(query).count() > 0:
            return render_template("signup.html", message="That email address already has an account.")
        else:
            document = {"firstname": fName, "lastname": lName, "username": usernameUp, "password": passwordUp,
                        "verified": False}
            db.loanUsers.insert_one(document)
            emailVerification(usernameUp)
            session['user'] = usernameUp

            return render_template("loanUser/signup.html",
                                   message="Your account has been created! Check your email to verify your account and get started! The link expires in an hour!")
    return render_template("loanUser/signup.html")


@signoutBlue.route("/signout")
def signout():
    if "user" in session:
        session.clear()
        return render_template("loanUser/login.html", message="Successfully logged out!")
    return render_template("loanUser/login.html", message="Make sure you are logged in!")


@loginBlue.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['user']
        password = request.form['pass']
        document = {"username": username, "password": password}
        userDocument = {"username": username}
        verifiedDocument = {"username": username, "password": password, "verified": True}
        # Make sure that account does exist
        if db.loanUsers.find(userDocument).count() > 0:
            # and credentials are correct
            if db.loanUsers.find(document).count() > 0:
                # and is email verified
                if db.loanUsers.find(verifiedDocument).count() > 0:
                    session['user'] = username
                    banknames=[]
                    allnames=[]
                    print("hello")
                    for item in db.bankUsers.find({}):
                        allnames.append(list(item.values()))
                    print(allnames)
                    for item in allnames:
                        banknames.append(item[1])
                    print(banknames)
                    return render_template("loanUser/questions_search.html", banks=banknames)
                else:
                    emailVerification(username)
                    return render_template("loanUser/login.html",
                                           message="Make sure your account has been verified. We resent the email!")
            else:
                return render_template("loanUser/login.html", message="Incorrect password.")
        else:
            return render_template("loanUser/login.html", message="An account with that email address does not exist.")
    return render_template("loanUser/login.html")


def emailVerification(emailTo):
    token = verificationKey.dumps(emailTo, salt='email-confirm')
    URL = f"http://localhost:5000/confirmEmail/{token}?username={emailTo}"

    # me == my email address
    # you == recipient's email address
    me = "alphapythonpeers@gmail.com"
    you = emailTo

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "CreditKonnect Verification"
    msg['From'] = me
    msg['To'] = you

    # Create the body of the message (a plain-text and an HTML version).
    text = f"Hi!\nClick on the following link to verify your account:\n{URL}"
    html = f"""\
    <html>
      <head></head>
      <body>
        <p>Hi!<br>
           Click on <a href="{URL}">this</a> link to verify your CreditKonnect user account.
        </p>
      </body>
    </html>
    """

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)
    # Send the message via local SMTP server.
    mail = smtplib.SMTP('smtp.gmail.com', 587)

    mail.ehlo()

    mail.starttls()

    mail.login('alphapythonpeers@gmail.com', 'Pencil!1')
    mail.sendmail(me, you, msg.as_string())
    mail.quit()


@confirmEmailBlue.route('/confirmEmail/<token>', methods=["GET"])
def confirmEmail(token):
    username = request.args.get('username')
    email = verificationKey.loads(token, salt='email-confirm', max_age=3600)
    myquery = {"username": username}
    newvalues = {"$set": {"verified": True}}

    db.loanUsers.update_one(myquery, newvalues)

    return render_template("loanUser/signup.html", message="Email confirmed. You can log in now!")


@searchBlue.route('/search', methods=["GET", "POST"])
def search():
    if "user" in session:
        if request.method == "POST":
            query = request.form['query']

            allQuestions = []
            allUsers = []
            endForm = []

            userDocuments = db.bankUsers.find({})
            for document in userDocuments:
                allUsers.append(list(document.values()))

            for item in allUsers:
                bankname = str(item[1])
                if query.lower() in bankname.lower():
                    bankNameUser = item[2]
                    bankCompleteName = item[1]

            questionDocuments = db.bankQuestions.find({})
            for document in questionDocuments:
                allQuestions.append(list(document.values()))

            for item in allQuestions:
                email = str(item[3])
                if bankNameUser.lower() == email.lower():
                    endForm.append(item)

            print(bankNameUser)
            print(endForm)
            print(bankCompleteName)


            return render_template("loanUser/questions_start.html", endForm=endForm, bankCompleteName=bankCompleteName)
        banknames=[]
        allnames=[]
        print("hello")
        for item in db.bankUsers.find({}):
            allnames.append(list(item.values()))
            print(allnames)
        for item in allnames:
                banknames.append(item[1])
                print(banknames)
    return render_template("loanUser/questions_search.html", endForm=None, banks=banknames)


@sendToBankBlue.route("/sendToBank", methods=["POST"])
def sendToBank():
    bankname = request.form["bankname"]
    print("Bank name to find email from: " + bankname)

    allQuestions = []
    endForm = []
    allUsers = []

    userDocuments = db.bankUsers.find({"bankname": bankname})
    for document in userDocuments:
        allUsers.append(list(document.values()))

    emailToSearch = allUsers[0][2]
    print("emailToSearch: " + emailToSearch)

    questionDocuments = db.bankQuestions.find({})
    for document in questionDocuments:
        allQuestions.append(list(document.values()))

    for item in allQuestions:
        email = str(item[3])
        print("Question email: " + email)
        if emailToSearch.lower() == email.lower():
            endForm.append(item)
    mm=[]
    print(endForm)
    allResponses = {}
    document = [('loanusername', session['user']), ('bankusername', emailToSearch)]
    allResponses.update(document)
    for item in endForm:
        prompt = str(item[1])
        min=int(item[4])
        max=int(item[5])
        mm.append(min)
        mm.append(max)
        print(prompt, min, max)
        answer = request.form[prompt]
        document = {prompt: answer}
        allResponses.update(document)
    print("Responses: ")
    print(list(allResponses.values()))
    responses=list(allResponses.values())
    pas=0
    for item in range(len(responses)-2):
        if int(mm[item*2])<int(responses[item+2])<int(mm[item*2+1]):
            pas=True
        else:
            pas=False
            break
    print(pas)
    banknames=[]
    allnames=[]
    print("hello")
    for item in db.bankUsers.find({}):
        allnames.append(list(item.values()))
        print(allnames)
    for item in allnames:
            banknames.append(item[1])
            print(banknames)
    db.bankResponses.insert_one(allResponses)
    sug=""
    thetruth="Passed"
    if pas==False:
        banknames.remove(bankname)
        print(banknames)
        sug=random.choice(banknames)
        print(sug)
        thetruth="Failed"
    
    return render_template("loanUser/questions_start.html", endForm=None,message="You "+thetruth, pas=pas, sug=sug, mess2="banks we think you will get a loan in:")

