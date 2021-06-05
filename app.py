from flask import Flask, session, abort, redirect, request
from flask_cors import CORS
from Google import Create_Service
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
from google.oauth2 import id_token
import google.auth.transport.requests
import os
import requests

CLIENT_SECRET_FILE = 'Client_Secret.json'
API_NAME = 'drive'
API_VERSION = 'v3'
SCOPES = ["https://www.googleapis.com/auth/drive",
          "https://www.googleapis.com/auth/userinfo.profile",
          "https://www.googleapis.com/auth/userinfo.email",
          "openid"]

service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
auth = HTTPBasicAuth()
app = Flask(__name__)
CORS(app)
api = Api(app)
app.secret_key = b'8q;\xc8Y.\xc0\x7f'

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "470181059605-uiii7hhq17aml3efcg1f7jr4da3tmkvh.apps.googleusercontent.com"

flow = Flow.from_client_secrets_file(
    client_secrets_file = CLIENT_SECRET_FILE,
    scopes = ["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email",
              "openid"],
    redirect_uri = "http://127.0.0.1:5000/callback"
)


def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function()

    return wrapper


class Login(Resource):
    def get(self):
        authorization_url, state = flow.authorization_url()
        session["state"] = state
        return redirect(authorization_url)


class CallBack(Resource):
    def get(self):
        flow.fetch_token(authorization_response = request.url)

        if not session["state"] == request.args["state"]:
            abort(500)  # State does not match!

        credentials = flow.credentials
        request_session = requests.session()
        cached_session = cachecontrol.CacheControl(request_session)
        token_request = google.auth.transport.requests.Request(session = cached_session)

        id_info = id_token.verify_oauth2_token(
            id_token = credentials._id_token,
            request = token_request,
            audience = GOOGLE_CLIENT_ID
        )

        session["google_id"] = id_info.get("sub")
        session["name"] = id_info.get("name")

        return redirect("/files")


class Logout(Resource):
    def get(self):
        session.clear()
        return redirect("/files")


# Lista todas as pastas (processos) a partir do folder_id
class ListarPastas(Resource):
    def get(self):
        folder_id = '1TSY3KWrVYZQY2SdTivbYgI1VdFjnoO4O'
        query = f"parents = '{folder_id}' and trashed=false and mimeType = 'application/vnd.google-apps.folder'"

        response = service.files().list(
            q = query,
            fields = 'nextPageToken, files(id, name, mimeType, webViewLink, iconLink, description)'
        ).execute()

        files = response.get('files')
        nextPageToken = response.get('nextPageToken')

        while nextPageToken:
            response = service.files().list(q = query, pageToken = nextPageToken).execute()
            files.extend(response.get('files'))
            nextPageToken = response.get('nextPageToken')

        return response


# lista todos os arquivos ou pastas a partir da pasta selecionada
class SelecionaPastas(Resource):
    def get(self, id):
        folder_id = id
        query = f"parents = '{folder_id}' and trashed=false and mimeType != 'application/vnd.google-apps.folder'"

        response = service.files().list(
            q = query,
            fields = 'nextPageToken, files(id, name, mimeType, webViewLink, iconLink)'
        ).execute()
        files = response.get('files')
        nextPageToken = response.get('nextPageToken')

        while nextPageToken:
            response = service.files().list(q = query, pageToken = nextPageToken).execute()
            files.extend(response.get('files'))
            nextPageToken = response.get('nextPageToken')

        return response


class Pesquisa(Resource):
    def get(self, nome):
        page_token = None
        folder_id = '1TSY3KWrVYZQY2SdTivbYgI1VdFjnoO4O'
        while True:
            response = service.files().list(
                q = f"parents = '{folder_id}' and fullText contains '{nome}' and mimeType = 'application/vnd.google-apps.folder' and trashed=false",
                fields = 'nextPageToken, files(id, name, mimeType, webViewLink, iconLink)',
                pageToken = page_token
            ).execute()
            for file in response.get('files', []):
                page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        return response


api.add_resource(ListarPastas, '/files')
api.add_resource(Login, '/login')
api.add_resource(CallBack, '/callback')
api.add_resource(Logout, '/logout')
api.add_resource(SelecionaPastas, '/processo/<string:id>')
api.add_resource(Pesquisa, '/pesquisa/<string:nome>')

if __name__ == '__main__':
    app.run(debug = True)
