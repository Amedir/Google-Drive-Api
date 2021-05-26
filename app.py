from flask import Flask, session, abort
from Google import Create_Service
from flask_restful import Resource, Api

CLIENT_SECRET_FILE = 'Client_Secret.json'
API_NAME = 'drive'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/drive']

service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
app = Flask(__name__)
api = Api(app)


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

        print(files[0])
        return files


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
        while True:
            response = service.files().list(
                q = f"fullText contains '{nome}' and mimeType = 'application/vnd.google-apps.folder' and trashed=false",
                fields = 'nextPageToken, files(id, name, mimeType, webViewLink, iconLink)',
                pageToken = page_token
            ).execute()
            for file in response.get('files', []):
                page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        return response



api.add_resource(ListarPastas, '/')
api.add_resource(SelecionaPastas, '/teste/<string:id>')
api.add_resource(Pesquisa, '/pesquisa/<string:nome>')

# /
# /paginaProcessos/
# /paginaEdição/
# /processos/<String:name>/
# /pesquisa/

if __name__ == '__main__':
    app.run(debug = True)
