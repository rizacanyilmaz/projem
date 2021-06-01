from flask import Flask, render_template, flash, redirect,url_for, session, logging, request
from flask_mysqldb import MySQL
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from wtforms import Form, StringField, TextAreaField,PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from flask import g, request, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu Sayfayı Görüntülemek İçin Öncelikle Giriş Yapmalısınız!","danger")
            return redirect(url_for("girisyap"))
    return decorated_function

class RegisterForm(Form):
    isim = StringField ("İsim Soyisim",validators=[validators.length(min = 3, max = 35, message="Lütfen en az 3, en fazla 35 karakter giriniz!")])
    kullaniciadi = StringField ("Kullanıcı Adı",validators=[validators.length(min = 5, max = 20, message="Lütfen en az 5, en fazla 20 karakter giriniz!")])
    email = StringField ("E-Mail Adresi",validators=[validators.Email(message="Lütfen Geçerli Bir E-Mail Adresi Giriniz!")])
    parola = PasswordField ("Şifre",validators=[validators.DataRequired(message="Lütfen Bir Şifre Giriniz!"),validators.EqualTo(fieldname="confirm",message="Girilen Şifreler Uyuşmuyor!")])
    confirm = PasswordField("Şifreyi Doğrula")

class LoginForm(Form):
    kullaniciadi = StringField("Kullanıcı Adı")
    parola = PasswordField("Parola")

class UserForm(Form):
    id = StringField("Kullanıcı Adı")
    parola = PasswordField("Parola")

class ArticleForm(Form):
    baslik = StringField("Sorununun Konusu Ne?", validators=[validators.Length(min=3, max=75)])
    icerik = TextAreaField("Sorunun Nedir?",validators=[validators.Length(min=5, max=2500)])

app = Flask(__name__)
admin = Admin(app)

app.secret_key = "projem"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "baybars"
app.config["MYSQL_PASSWORD"] = "Baybars.4dec"
app.config["MYSQL_DB"] = "projem"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

@app.route("/")
def index():
    return render_template ("anasayfa.html")

@app.route("/içerik/<string:id>")
def detail(id):
    return "içerikid" + id

@app.route("/yardımedebileceklerimiz")
def yardımedebileceklerimiz():
    return render_template ("yardımedebileceklerimiz.html")

@app.route("/iletişimadresleri")
def iletisimadresleri():
    return render_template ("iletişimadresleri.html")

@app.route("/haftaninfilmi")
def haftaninfilmi():
    return render_template ("haftaninfilmi.html")

@app.route("/kontrolpaneli")
@login_required
def kontrolpaneli():
    cursor = mysql.connection.cursor()
    sorgu = "Select*From sorunlar Where yazar = %s"
    result = cursor.execute(sorgu,(session["kullaniciadi"],))
    if result > 0:
        sorunlar = cursor.fetchall()
        return render_template("kontrolpaneli.html",sorunlar = sorunlar)
    else:
        return render_template("kontrolpaneli.html")


@app.route("/sorunbildir")
@login_required
def sorunbildir():
    return render_template ("sorunbildir.html")

@app.route("/sorunlar")
def sorunlar():
    cursor = mysql.connection.cursor()
    
    sorgu = "Select*From sorunlar"
    result = cursor.execute(sorgu)
    if result > 0:
        sorunlar = cursor.fetchall()
        return render_template("sorunlar.html",sorunlar = sorunlar)

    else:
        return render_template("sorunlar.html")

@app.route("/kayitol", methods = ["GET","POST"])
def kayitol():
    form = RegisterForm(request.form)
    if request.method =="POST" and form.validate():
        isim = form.isim.data
        kullaniciadi = form.kullaniciadi.data
        email = form.email.data
        parola = sha256_crypt.encrypt(form.parola.data)

        cursor = mysql.connection.cursor()
        sorgu = "Insert into kayitlar (isim,kullaniciadi,email,parola) VALUES (%s,%s,%s,%s)"
        cursor.execute(sorgu, (isim,kullaniciadi,email,parola))
        mysql.connection.commit()
        cursor.close()
        flash("Kaydınız Başarılı Bir Şekilde Gerçekleştirilmiştir!","success")
        return redirect(url_for("girisyap"))

    else:
        return render_template("kayitol.html", form = form)

@app.route("/girisyap",methods =["GET","POST"])
def girisyap():
    form = LoginForm(request.form)
    if request.method == "POST":
        kullaniciadi = form.kullaniciadi.data
        password_entered = form.parola.data
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM kayitlar where kullaniciadi = %s"
        result = cursor.execute(sorgu,(kullaniciadi,))
        if result > 0:
            data = cursor.fetchone()
            real_password = data["parola"]
            if sha256_crypt.verify(password_entered, real_password):
                flash("Başarılı Bir Şekilde Giriş Yaptınız.","success")
                session["logged_in"] = True
                session["kullaniciadi"] = kullaniciadi
                return redirect(url_for("yardımedebileceklerimiz"))
            else:
                flash("Parolanızı Kontrol Ediniz!","danger")
                return redirect(url_for("girisyap"))
        else:
            flash("Böyle Bir Kullanıcı Bulunamadı!","danger")
            return redirect(url_for("girisyap"))
    return render_template ("girisyap.html",form=form)

@app.route("/cıkısyap")
def cıkısyap():
    session.clear()
    return redirect(url_for("index"))

@app.route("/sorun/<string:id>")
@login_required
def sorun(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select*From sorunlar Where id = %s"
    result = cursor.execute(sorgu,(id),)
    if result > 0:
        sorun = cursor.fetchone()
        return render_template("sorun.html",sorun = sorun)
    else:
        return render_template("sorun.html")

@app.route("/sorunekle", methods=["GET","POST"])
def sorunekle():
    form = ArticleForm(request.form)
    if request.method =="POST" and form.validate():
        baslik = form.baslik.data
        icerik = form.icerik.data
        
        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO sorunlar(baslik,yazar,icerik) VALUES (%s,%s,%s)"
        cursor.execute (sorgu,(baslik,session["kullaniciadi"],icerik))
        mysql.connection.commit()
        cursor.close()
        flash("Sorununuz Başarılı Bir Şekilde Eklenmiştir","success")
        return redirect(url_for("kontrolpaneli"))

    return render_template("sorunekle.html",form = form)

@app.route("/sil/<string:id>")
@login_required
def sil(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * From sorunlar where yazar = %s and id = %s"
    result = cursor.execute(sorgu,(session["kullaniciadi"],id))
    if result > 0:
        sorgu2 = "Delete From sorunlar where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("kontrolpaneli"))
    else:
        flash("Böyle Bir Sorun Yok veya Bu İşleme Yetkiniz Bulunamadı","danger")
        return redirect(url_for("index"))

@app.route("/düzenle/<string:id>", methods=["GET","POST"])
@login_required
def düzenle(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "Select * From sorunlar where id = %s and yazar = %s"
        result = cursor.execute(sorgu,(id,session["kullaniciadi"]))
        if result == 0:
            flash("Böyle Bir Sorun Yok veya Bu İşleme Yetkiniz Bulunamadı","danger")
            return redirect(url_for("index"))
        else:
            sorun = cursor.fetchone()
            form = ArticleForm()
            
            form.baslik.data = sorun["baslik"]
            form.icerik.data = sorun["icerik"]
            return render_template("guncelle.html",form = form)
    else:
            form = ArticleForm(request.form)
            yeniBaslik = form.baslik.data
            yeniİcerik = form.icerik.data
            
            sorgu2 = "Update sorunlar Set baslik = %s,icerik = %s where id = %s"
            cursor = mysql.connection.cursor()
            cursor.execute(sorgu2,(yeniBaslik,yeniİcerik,id))
            mysql.connection.commit()
            flash("Sorununuz Başarılı Bir Şekilde Güncellenmiştir.","success")
            return redirect(url_for("kontrolpaneli"))

@app.route("/search",methods=["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM sorunlar WHERE baslik LIKE '%" + keyword + "%'"
        result = cursor.execute(sorgu)

        if result == 0:
            flash("Aramanıza Uygun Sorun Bulunamadı.","warning")
            return redirect(url_for("sorunlar"))
        else:
            sorunlar = cursor.fethcall()
            return render_template("sorunlar.html",sorunlar=sorunlar)

if __name__ == ("__main__"):
    app.run (debug=True)