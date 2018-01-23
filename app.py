import os
import random
from functools import wraps

from flask import Flask, url_for, jsonify, render_template, request, abort
from flask_cors import CORS
from gevent import monkey

from static.cats import cats
from static.why import why

monkey.patch_all()
application = Flask(__name__)
cors = CORS(application, resources={r"/api/*": {"origins": "*"}})
application.config['PROPAGATE_EXCEPTIONS'] = False
keys = []
application.config['JSON_AS_ASCII'] = False


def require_appkey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.headers.get('Key') and request.headers.get('Key') in keys:
            return view_function(*args, **kwargs)
        else:
            abort(401)

    return decorated_function


def new_rnd(cat):
    names = os.listdir(os.path.join(application.static_folder, '/var/www/nekoapi/' + cat))
    random.shuffle(names)
    img_url = url_for('static', filename=os.path.join(cat, random.choice(names)))
    return img_url


def random_image(x):
    names = os.listdir(os.path.join(application.static_folder, x))
    random.shuffle(names)
    img_url = url_for('static', filename=os.path.join(x, random.choice(names)))
    return img_url


@application.route('/')
def neko():
    random.shuffle(cats)
    c = random.choice(cats)
    return render_template('neko.html', img_url=random_image("neko"), cat=c)


@application.route('/lewd')
def nsfwneko():
    random.shuffle(cats)
    c = random.choice(cats)
    return render_template('nsfwneko.html', img_url=random_image("nya"), cat=c)


@application.route('/api/neko')
def nekos():
    link = 'https://nekos.life' + random_image("neko")
    return jsonify(neko=link)


@application.route('/api/lewd/neko')
def lewdnekos():
    link = 'https://nekos.life' + random_image("nya")
    return jsonify(neko=link)


@application.route('/api/pat')
def pat():
    link = 'https://nekos.life' + random_image("pat")
    return jsonify(url=link)


@application.route('/api/hug')
def hug():
    link = 'https://nekos.life' + random_image("hug")
    return jsonify(url=link)


@application.route('/api/kiss')
def kiss():
    link = 'https://nekos.life' + random_image("kiss")
    return jsonify(url=link)


@application.route('/api/lizard')
def lizard():
    link = 'https://nekos.life' + random_image("lizard")
    return jsonify(url=link)


@application.route('/api/why')
def whyy():
    whytho = random.choice(why)
    return jsonify(why=whytho)


# all v2 stuff
@application.route('/api/v2/img/<string:cat>')
def new(cat):
    link = 'https://cdn.nekos.life' + new_rnd(cat)
    clink = link.replace('/static', '')
    return jsonify(url=clink)


@application.route('/api/v2/why')
def _w():
    random.shuffle(why)
    w = random.choice(why)
    return jsonify(why=w)


@application.route('/api/v2/cat')
def _c():
    random.shuffle(cats)
    c = random.choice(cats)
    return jsonify(cat=c)


if __name__ == '__main__':
    application.run(host="0.0.0.0", threaded=True)
