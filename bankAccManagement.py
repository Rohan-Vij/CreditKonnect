# flask import
from flask import Flask, render_template, request, session, Blueprint, g
# mongodb import
from pymongo import MongoClient
# packages for email sending
from itsdangerous import URLSafeTimedSerializer
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# MongoDB Cloud Database connection (using Azure server)
client = MongoClient(
    'mongodb+srv://mainUser:mainUserPass@fastapproval.f06cc.azure.mongodb.net/fastapproval?retryWrites=false&w=majority')
db = client["fastapproval"]
# Email sending initializing
verificationKey = URLSafeTimedSerializer('Thisisasecret!')

homePageBlueBank = Blueprint('homePageBank', __name__, template_folder='templates')
signupBlueBank = Blueprint('signupBank', __name__, template_folder='templates')
signoutBlueBank = Blueprint('signoutBank', __name__, template_folder='templates')
loginBlueBank = Blueprint('loginBank', __name__, template_folder='templates')
confirmEmailBlueBank = Blueprint('confirmEmailBank', __name__, template_folder='templates')
addQuestionsBlueBank = Blueprint('addQuestions', __name__, template_folder='templates')


@addQuestionsBlueBank.route('/banks/questions', methods=["GET", "POST"])
def addQuestions():
    if request.method == "POST":
        prompt = request.form['prompt']
        type = request.form['type']
        min=request.form['min']
        max=request.form['max']
        user = getUser(session['user'])
        user = user[0][2]
        print(prompt + type)
        document = {"question": prompt,
                    "type": type,
                    "username": user,
                    "min":min,
                    "max":max}
        db.bankQuestions.insert_one(document)

        currentQuestions = getQuestions()

        currentResponses = getResponses()
        if currentResponses != [[], []]:
            responseValues = currentResponses[0]
            responseNames = currentResponses[1][0]
            responseNames = responseNames[3:]

            print(responseValues)
            print(responseNames)
        else:
            responseValues = []
            responseNames = []

        return render_template("bankUser/questions.html", questions=currentQuestions, responseValues=responseValues,
                               responseNames=responseNames)

    currentQuestions = getQuestions()
    currentResponses = getResponses()
    if currentResponses != [[], []]:
        responseValues = currentResponses[0]
        responseNames = currentResponses[1][0]
        responseNames = responseNames[3:]

        print(responseValues)
        print(responseNames)
    else:
        responseValues = []
        responseNames = []

    print(responseValues)
    print(responseNames)

    return render_template("bankUser/questions.html", questions=currentQuestions, responseValues=responseValues, responseNames=responseNames)


@homePageBlueBank.route("/banks")
def homepageBank():
    return render_template("bankUser/landing_page.html")


@signupBlueBank.route("/banks/signup", methods=["GET", "POST"])
def signupBank():
    if request.method == "POST":
        bname = request.form['bname']
        usernameUp = request.form['user']
        passwordUp = request.form['pass']
        query = {"username": usernameUp}
        # Checking if the chosen username exists
        if db.bankUsers.find(query).count() > 0:
            return render_template("bankUser/signup.html", message="That email address already has an account.")
        else:
            document = {"bankname": bname, "username": usernameUp, "password": passwordUp,
                        "verified": False}
            db.bankUsers.insert_one(document)
            emailVerificationBank(usernameUp)
            session['user'] = usernameUp

            return render_template("bankUser/signup.html",
                                   message="Your account has been created! Check your email to verify your account and get started! The link expires in an hour!")
    return render_template("bankUser/signup.html")


@signoutBlueBank.route("/banks/signout")
def signoutBank():
    if "user" in session:
        session.clear()
        return render_template("bankUser/login.html", message="Successfully logged out!")
    return render_template("bankUser/login.html", message="Make sure you are logged in!")


@confirmEmailBlueBank.route("/banks/login", methods=["GET", "POST"])
def loginBank():
    if request.method == "POST":
        username = request.form['user']
        password = request.form['pass']
        document = {"username": username, "password": password}
        userDocument = {"username": username}
        verifiedDocument = {"username": username, "password": password, "verified": True}
        # Make sure that account does exist
        if db.bankUsers.find(userDocument).count() > 0:
            # and credentials are correct
            if db.bankUsers.find(document).count() > 0:
                # and is email verified
                if db.bankUsers.find(verifiedDocument).count() > 0:
                    session['user'] = username
                    currentQuestions = getQuestions()
                    currentResponses = getResponses()
                    if currentResponses != [[], []]:
                        responseValues = currentResponses[0]
                        responseNames = currentResponses[1][0]
                        responseNames = responseNames[3:]

                        print(responseValues)
                        print(responseNames)
                    else:
                        responseValues = []
                        responseNames = []

                    print(responseValues)
                    print(responseNames)

                    return render_template("bankUser/questions.html", questions=currentQuestions,
                                           responseValues=responseValues, responseNames=responseNames)
                    return render_template("bankUser/questions.html")
                else:
                    emailVerificationBank(username)
                    return render_template("bankUser/login.html",
                                           message="Make sure your account has been verified. We resent the email!")
            else:
                return render_template("bankUser/login.html", message="Incorrect password.")
        else:
            return render_template("bankUser/login.html", message="An account with that email address does not exist.")
    return render_template("bankUser/login.html")


def emailVerificationBank(emailTo):
    token = verificationKey.dumps(emailTo, salt='email-confirm')
    URL = f"http://localhost:5000/banks/confirmEmailBank/{token}?username={emailTo}"

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


@confirmEmailBlueBank.route('/banks/confirmEmailBank/<token>', methods=["GET"])
def confirmEmailBank(token):
    username = request.args.get('username')
    email = verificationKey.loads(token, salt='email-confirm', max_age=3600)
    myquery = {"username": username}
    newvalues = {"$set": {"verified": True}}

    db.bankUsers.update_one(myquery, newvalues)

    return render_template("bankUser/login.html", message="Email confirmed. You can log in now!")


def getUser(user):
    userDocuments = db.bankUsers.find({"username": user})
    users = []
    for userDocument in userDocuments:
        users.append(list(userDocument.values()))
    return users


def getQuestions():
    currentQuestions = []
    questions = db.bankQuestions.find({"username": session['user']})
    for item in questions:
        currentQuestions.append(list(item.values()))

    return currentQuestions


def getResponses():
    currentResponses = []
    questionNames = []
    questions = db.bankResponses.find({"bankusername": session['user']})
    i = 0
    for item in questions:
        currentResponses.append(list(item.values()))
        if i == 0:
            questionNames.append(list(item.keys()))
            i += 1



    return [currentResponses, questionNames]
