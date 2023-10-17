import json

import cherrypy
import dkcsvdb
from jinja2 import Environment, FileSystemLoader


class TableApp:
    def __init__(self, csv_filename):
        self.db = dkcsvdb.connect(csv_filename)
        self.template_env = Environment(loader=FileSystemLoader('templates'))
        self.error_message = None

    def render_template(self, headers, entries, error=None):
        template = self.template_env.get_template('table_template.html')
        return template.render(headers=headers, entries=entries, error=error)

    @cherrypy.expose
    def index(self):
        # Lesen der Einträge aus der CSV-Datei
        entries = self.db.fetch()
        if entries:
            rendered_html = self.render_template(entries[0].keys(), entries)
        else:

            # Wenn keine Einträge gefunden wurden
            error_message = "Es wurden keine Eintraege gefunden."
            rendered_html = self.render_template([], [], error=error_message)

        return rendered_html

    @cherrypy.expose
    def fetch_data(self, filter=None):

        # Bisherigen Fehlerstatus loeschen
        self.error_message = None

        # Ruft die `fetch`-Methode aus dkcsvdb.py mit dem gegebenen Filter auf
        if filter:
            entries = self.db.fetch(name=filter)
        else:
            entries = self.db.fetch()

        if entries:
            rendered_html = self.render_template(entries[0].keys(), entries)
        else:

            # Wenn keine Einträge gefunden wurden
            error_message = "Es wurden keine Eintraege gefunden."
            rendered_html = self.render_template([], [], error=error_message)

        return rendered_html

    @cherrypy.expose
    def insert_data(self, data=None):
        # Bisherigen Fehlerstatus löschen
        self.error_message = None

        # Überprüfen, ob `data` nicht leer ist
        if data:
            # Konvertieren von `data`
            try:
                data_dict = json.loads(data)
                # Aufruf der `insert`-Methode in `dkcsvdb`, um die Daten in die CSV-Datei einzufügen
                self.db.insert(data_dict)
            except json.JSONDecodeError as e:
                self.error_message = "Es wurden keine gültigen JSON-Daten eingegeben: " + str(e)
                rendered_html = self.render_template([], [], error=self.error_message)
                return rendered_html

        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def update_data(self, data=None):
        # Bisherigen Fehlerstatus löschen
        self.error_message = None

        # Überprüfen, ob `data` nicht leer ist
        if data:
            try:
                data_dict = json.loads(data)

                if 'name' not in data_dict:
                    self.error_message = "Das Feld 'name' fehlt in den Aktualisierungsdaten."
                    rendered_html = self.render_template([], [], error=self.error_message)
                    return rendered_html
                else:

                    # Aufruf der `update`-Methode in `dkcsvdb`, um die Daten in die CSV-Datei einzufügen
                    self.db.update(data_dict)
            except json.JSONDecodeError as e:
                self.error_message = "Es wurden keine gültigen JSON-Daten eingegeben: " + str(e)
                rendered_html = self.render_template([], [], error=self.error_message)
                return rendered_html
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def delete_data(self, filter=None):

        # Bisherigen Fehlerstatus loeschen
        self.error_message = None

        # Ruft die `delete`-Methode aus dkcsvdb.py mit dem gegebenen Filter auf
        if filter:
            self.db.delete(name=filter)
        else:
            # Kein Filter angegeben, löschen Sie alle Einträge
            try:
                self.db.delete()
            except Exception as e:
                self.error_message = "Beim Löschen ist ein Fehler aufgetreten: " + str(e)

        raise cherrypy.HTTPRedirect('/')


if __name__ == '__main__':
    csv_filename = 'some-file.csv'
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 8081,
    })
    cherrypy.quickstart(TableApp(csv_filename))
