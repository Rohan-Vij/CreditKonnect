from loanAccManagement import *
from bankAccManagement import *

# Flask app initializing
app = Flask(__name__)
app.secret_key = "fastandspeedy"
# from loanAccManagement
app.register_blueprint(homePageBlue)
app.register_blueprint(signupBlue)
app.register_blueprint(signoutBlue)
app.register_blueprint(loginBlue)
app.register_blueprint(confirmEmailBlue)
app.register_blueprint(searchBlue)
app.register_blueprint(sendToBankBlue)

# from bankAccManagement
app.register_blueprint(homePageBlueBank)
app.register_blueprint(signupBlueBank)
app.register_blueprint(signoutBlueBank)
app.register_blueprint(loginBlueBank)
app.register_blueprint(confirmEmailBlueBank)
app.register_blueprint(addQuestionsBlueBank)



if __name__ == "__main__":
    app.run()
