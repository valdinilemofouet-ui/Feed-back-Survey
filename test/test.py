from flask import Flask, redirect, render_template, url_for, request, session, flash 
from datetime import timedelta

app=Flask(__name__)
app.secret_key="hello12"
app.permanent_session_lifetime=timedelta(minutes=5)
 
@app.route("/")
def home():
    return render_template("index.html",content=["valdini","genie","ines"])

@app.route("/user")
def user_profile():
    if "user" in session:
        user=session['user']
        return render_template("index.html", content=[user])
    else:
        return redirect(url_for("login"))
# @app.route("/admin")
# def admin():
#     return redirect(url_for("user_profile", username="Administrator"))

@app.route("/survey")
def survey():
    return render_template("survey.html")


@app.route("/login", methods=["POST","GET"])
def login():
    if request.method=="POST":
        user=request.form["username"]
        session["user"]=user
        session.permanent=True
        flash("Login Successful!", "info")
        return redirect(url_for("user_profile"))
    else:
        if "user" in session:
            return redirect(url_for("user_profile"))
        return render_template("login.html")
    
@app.route("/logout")
def logout():
    if "user" in session:

        session.pop("user",None)
        flash("You have been logged out!", "info")
    return redirect(url_for("login"))

# @app.route("/user")
# def user(usr):
#     return f"<h1>Hello {usr}!</h1>"

if __name__ == '__main__':
    app.run(debug=True)