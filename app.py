import gevent.monkey

# gevent for async
# patch first to avoid recursion errors with oauth on callback
gevent.monkey.patch_all()

import os
import random
import sys
import re
from functools import wraps

from flask import jsonify, abort, Flask, request, redirect, url_for, flash, render_template, session
from flask_cors import CORS
from requests_oauthlib import OAuth2Session

from config import OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET, OAUTH2_REDIRECT_URI, API_BASE_URL, AUTHORIZATION_BASE_URL, \
    TOKEN_URL, LEWD_UPLOAD_FOLDER, NEKO_UPLOAD_FOLDER, PAT_UPLOAD_FOLDER, HUG_UPLOAD_FOLDER, KISS_UPLOAD_FOLDER, \
    CUDDLE_UPLOAD_FOLDER, LIZARD_UPLOAD_FOLDER, ALLOWED_EXTENSIONS, IDS, SECRET_KEY
from static.cats import cats
from static.why import why
from static.facts import facts

from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer

application = Flask(__name__)
# Cross-Origin Resource Sharing
cors = CORS(application, resources={r"/*": {"origins": "*"}})
# debug
if any('debug' in arg.lower() for arg in sys.argv):
    application.debug = True
    application.config['PROPAGATE_EXCEPTIONS'] = True
# old/maybe for sharex or something
keys = []
# False for utf8/uni
application.config['JSON_AS_ASCII'] = False
application.config["SECRET_KEY"] = SECRET_KEY

neko_bot = ChatBot("neko",
                   preprocessors=[
                       'chatterbot.preprocessors.clean_whitespace',
                       'chatterbot.preprocessors.unescape_html',
                       'chatterbot.preprocessors.convert_to_ascii'
                   ],
                   filters=["chatterbot.filters.RepetitiveResponseFilter"],
                   storage_adapter="chatterbot.storage.MongoDatabaseAdapter",
                   database='nekos_life1',
                   logic_adapters=[
                       {
                           "import_path": "chatterbot.logic.BestMatch",
                           "statement_comparison_function": "chatterbot.comparisons.levenshtein_distance",
                           "response_selection_method": "chatterbot.response_selection.get_first_response"
                       },
                       {
                           'import_path': 'chatterbot.logic.SpecificResponseAdapter',
                           'input_text': 'Help me!',
                           'output_text': 'Ok, here is a link: https://nekos.life/'

                       },
                       {
                           'import_path': 'chatterbot.logic.SpecificResponseAdapter',
                           'input_text': 'who made you?',
                           'output_text': 'Tails'

                       }
                   ])
neko_bot.set_trainer(ChatterBotCorpusTrainer)
neko_bot.train("chatterbot.corpus.english")

if 'http://' in OAUTH2_REDIRECT_URI:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'
# we'll let cf handle this
if 'https://' in OAUTH2_REDIRECT_URI:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'


def get_owo(text):
    faces = ["owo", "UwU", ">w<", "^w^"]
    v = text
    r = re.sub('[rl]', "w", v)
    r = re.sub('[RL]', "W", r)
    r = re.sub('ove', 'uv', r)
    r = re.sub('n', 'ny', r)
    r = re.sub('N', 'NY', r)
    r = re.sub('[!]', " " + random.choice(faces) + " ", r)
    return r


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=OAUTH2_CLIENT_ID,
        token=token,
        state=state,
        scope=scope,
        redirect_uri=OAUTH2_REDIRECT_URI,
        auto_refresh_kwargs={
            'client_id': OAUTH2_CLIENT_ID,
            'client_secret': OAUTH2_CLIENT_SECRET,
        },
        auto_refresh_url=TOKEN_URL,
        token_updater=token_updater)


def token_updater(token):
    session['oauth2_token'] = token


# for @require_appkey
def require_appkey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.headers.get('Key') and request.headers.get('Key') in keys:
            return view_function(*args, **kwargs)
        else:
            abort(401)

    return decorated_function


def random_image(cat):
    names = os.listdir(os.path.join('/var/www/nekoapi/' + cat))
    random.shuffle(names)
    img_url = 'https://cdn.nekos.life/' + os.path.join(cat, random.choice(names))
    return img_url


def random_ball():
    names = os.listdir(os.path.join('/var/www/nekoapi/8ball/'))
    name = random.choice(names)
    res = os.path.splitext(os.path.basename(name))[0].replace("_", " ").replace("Youre", "You're")
    random.shuffle(names)
    img_url = 'https://cdn.nekos.life/' + os.path.join('8ball/', name)
    return res, img_url


@application.route('/api/v2/8ball')
def ball():
    res, img_url = random_ball()
    return jsonify(response=res, url=img_url)


@application.route('/')
def index():
    random.shuffle(cats)
    c = random.choice(cats)
    return render_template('index.html', img_url=random_image("neko"), cat=c)


@application.route('/lewd')
def nsfwneko():
    random.shuffle(cats)
    c = random.choice(cats)
    return render_template('nsfwneko.html', img_url=random_image("lewd"), cat=c)


# DEPRECATED
@application.route('/api/neko')
def nekos():
    return jsonify(neko=random_image("neko"))


# DEPRECATED
@application.route('/api/lewd/neko')
def lewdnekos():
    link = random_image("lewd")
    return jsonify(neko=link)


# DEPRECATED
@application.route('/api/pat')
def pat():
    link = random_image("pat")
    return jsonify(url=link)


# DEPRECATED
@application.route('/api/hug')
def hug():
    link = random_image("hug")
    return jsonify(url=link)


# DEPRECATED
@application.route('/api/kiss')
def kiss():
    link = random_image("kiss")
    return jsonify(url=link)


# DEPRECATED
@application.route('/api/lizard')
def lizard():
    link = random_image("lizard")
    return jsonify(url=link)


# DEPRECATED
@application.route('/api/why')
def huh():
    w = random.choice(why)
    return jsonify(why=w)


# all v2 stuff #


# lol im lazy have docs :^)
@application.route('/api/v2/endpoints')
def list_routes():
    import urllib.parse
    output = []
    for rule in application.url_map.iter_rules():
        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg).replace("[cat]",
                                                       str([name for name in os.listdir('/var/www/nekoapi/') if
                                                            name != "old"]).replace("[", "<").replace("]", ">")
                                                       )
        methods = ','.join(rule.methods)
        url = url_for(rule.endpoint, **options)
        if "v2" in str(url):
            line = urllib.parse.unquote(
                "{:20s} {}".format(methods, url))
            output.append(line)

        if "api" in str(url) and "v2" not in str(url):
            line = urllib.parse.unquote(
                "{:20s} {} -DEPRECATED".format(methods, url))
            output.append(line)
    return jsonify(sorted(output))


@application.route("/api/v2/chat")
def get_neko_response():
    if request.headers.get('text'):
        if len(request.headers.get('text')) > 200 or len(request.headers.get('text')) < 1:
            return jsonify(msg="oopsie whoopsie you made a fucky wucky, no text or text over 200")

        if request.headers.get('owo') and request.headers.get('owo').lower() == "true":
            input_msg = request.headers.get('text')
            return jsonify(response=str(get_owo(str(neko_bot.get_response(input_msg)))))

        input_msg = request.headers.get('text')
        return jsonify(response=str(neko_bot.get_response(input_msg)))

    if request.args.get('text'):
        if len(request.args.get('text')) > 200 or len(request.args.get('text')) < 1:
            return jsonify(msg="oopsie whoopsie you made a fucky wucky, no text or text over 200")

        if request.args.get('owo') and request.args.get('owo').lower() == "true":
            input_msg = request.args.get('text')
            return jsonify(response=str(get_owo(str(neko_bot.get_response(input_msg)))))

        input_msg = request.args.get('text')
        return jsonify(response=str(neko_bot.get_response(input_msg)))

    else:
        return jsonify(msg="oopsie whoopsie you made a fucky wucky, no text or text over 200")


@application.route('/api/v2/owoify')
def owoify():
    if request.args.get('text'):
        if len(request.args.get('text')) > 200 or len(request.args.get('text')) < 1:
            return jsonify(msg="oopsie whoopsie you made a fucky wucky, no text or text over 200")

        return jsonify(owo=str(get_owo(request.args.get('text'))))
    else:
        return jsonify(msg="oopsie whoopsie you made a fucky wucky, no text or text over 200")


@application.route('/api/v2/img/<string:cat>')
def new(cat):
    try:
        link = random_image(cat)
        return jsonify(url=link)
    except Exception as e:
        print(e)
        return jsonify(msg="404")


@application.route('/api/v2/why')
def _w():
    w = random.choice(why)
    return jsonify(why=w)


@application.route('/api/v2/fact')
def _f():
    f = random.choice(facts)
    return jsonify(fact=f)


@application.route('/api/v2/cat')
def _c():
    random.shuffle(cats)
    c = random.choice(cats)
    return jsonify(cat=c)


# oauth/upload
@application.route('/upload/', methods=['GET', 'POST'])
def upload():
    if 'userid' in session:
        if session['userid'] in IDS:
            if request.method == 'POST':
                if 'file[]' not in request.files:
                    flash('No file part')
                    return redirect(request.url)
                files = request.files.getlist("file[]")
                print("owo")
                for file in files:
                    print(file)
                    if not allowed_file(file.filename):
                        flash(u'bad file', 'error')
                    if file.filename == '':
                        flash('No selected file')
                        return redirect(request.url)
                    if file and allowed_file(file.filename):
                        n, l, k, h, p, c, li = "neko", "lewd", "kiss", "hug", "pat", "cuddle", "lizard"
                        option = request.form['type']
                        print(option)
                        d = ""
                        if option == n:
                            d = NEKO_UPLOAD_FOLDER
                        if option == l:
                            d = LEWD_UPLOAD_FOLDER
                        if option == k:
                            d = KISS_UPLOAD_FOLDER
                        if option == h:
                            d = HUG_UPLOAD_FOLDER
                        if option == p:
                            d = PAT_UPLOAD_FOLDER
                        if option == c:
                            d = CUDDLE_UPLOAD_FOLDER
                        if option == li:
                            d = LIZARD_UPLOAD_FOLDER
                        filename = file.filename
                        print(d)
                        destination = "".join([d, filename])
                        print("Accept incoming file:", filename)
                        print(destination)
                        file.save(destination)
                        flash(u'uploaded', 'success')
                return redirect(url_for('rel'))
            random.shuffle(cats)
            ca = random.choice(cats)
            return render_template('upload.html', cat=ca)

        else:
            return "401"
    else:
        return redirect(url_for('login'))


@application.route('/release/')
def rel():
    if 'userid' in session:
        if session['userid'] in IDS:
            n, l, k, h, p, c, li = os.listdir(NEKO_UPLOAD_FOLDER), os.listdir(LEWD_UPLOAD_FOLDER), os.listdir(
                KISS_UPLOAD_FOLDER), os.listdir(HUG_UPLOAD_FOLDER), os.listdir(PAT_UPLOAD_FOLDER), os.listdir(
                CUDDLE_UPLOAD_FOLDER), os.listdir(LIZARD_UPLOAD_FOLDER)
            random.shuffle(cats)
            ca = random.choice(cats)
            return render_template('list.html', nekos=n, lewds=l, kisses=k, hugs=h, pats=p, cuddles=c, lizards=li,
                                   cat=ca)
        else:
            return "401"
    else:
        return redirect(url_for('login'))


@application.route('/login/')
def login():
    scope = request.args.get(
        'scope',
        'identify')
    discord = make_session(scope=scope.split(' '))
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth2_state'] = state
    return redirect(authorization_url)


@application.route('/callback/')
def callback():
    if request.values.get('error'):
        return request.values['error']
    discord = make_session(state=session.get('oauth2_state'))
    token = discord.fetch_token(
        TOKEN_URL,
        client_secret=OAUTH2_CLIENT_SECRET,
        authorization_response=request.url)
    session['oauth2_token'] = token
    discord = make_session(token=session.get('oauth2_token'))
    userinfo = discord.get(API_BASE_URL + '/users/@me').json()
    session['username'] = userinfo['username']
    session['avatar'] = userinfo['avatar']
    session['userid'] = userinfo['id']
    if session['userid'] in IDS:
        return redirect(url_for('.upload'))
    else:
        session.clear()
        return "401"


@application.route('/logout/')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    application.run(host="0.0.0.0", threaded = True)
