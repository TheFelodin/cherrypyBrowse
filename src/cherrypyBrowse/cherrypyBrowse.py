import cherrypy
import dkcsvdb
import json
import os
import pathlib

from jinja2 import Environment, FileSystemLoader


SRC_DIR = pathlib.Path(__file__).parent.parent

cherrypy.config.update({
    'server.socket_host': '127.0.0.1',
    'server.socket_port': 8081,
    'tools.staticdir.on': True,
    'tools.staticdir.dir': SRC_DIR / 'static'
})


class TableApp:
    def __init__(self, csv_filename):
        self.csv_filename = csv_filename
        self.csv_backup = str(csv_filename).replace(".csv", ".backup")
        self._copy_file(self.csv_filename, self.csv_backup)
        self.db = dkcsvdb.connect(csv_filename)
        self.template_env = Environment(loader=FileSystemLoader(SRC_DIR / 'templates'))
        self.error_message = None

    def render_template(self, headers, entries, error=None):
        """
        Creates a hmtl file displaing data in a table.

        Args:
            headers: Table headers
            entries: Data shown in the table
            error: Error message to display

        Returns: dynamic generated HTML
        """

        template = self.template_env.get_template('table_template.html')
        return template.render(headers=headers, entries=entries, error=error)


    @cherrypy.expose
    def index(self, filter=None):
        """
        Collects data from file

        Args:
            filter: name given via input field

        Returns: dynamic generated HTML displaying selected entries or error message
        """

        if cherrypy.request.params.get("filter") == "":
            raise cherrypy.HTTPRedirect('/')

        self.error_message = None

        # fetches data by filter or all if no filter is given
        if filter:
            entries = self.db.fetch(name=filter)
        else:
            entries = self.db.fetch()

        # creates HTML with selected entries
        if entries:
            rendered_html = self.render_template(entries[0].keys(), entries)
        else:

            # if no entries are found return error message
            error_message = "No entries found."
            rendered_html = self.render_template([], [], error=error_message)

        return rendered_html

    @cherrypy.expose
    def insert_data(self, data=None):
        """
        Adds entry to database.

        Args:
            data: e.g. {"name": "schmidt", "street": "dorfstr"}. JSON formated entry with keys "name" & "street"

        Returns: dynamic generated HTML of all entries
        """

        self.error_message = None
        if data:
            try:
                # convert input to JSON
                data_dict = json.loads(data)
                self.db.insert(data_dict)

            # if no valid JSON string was given, return error
            except json.JSONDecodeError as e:
                self.error_message = "No valid JSON-data was given:<br>" + str(e)
                rendered_html = self.render_template([], [], error=self.error_message)
                return rendered_html
        else:
            self.error_message = "No input detected.<br>Please enter valid JSON."
            rendered_html = self.render_template([], [], error=self.error_message)
            return rendered_html

        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def update_data(self, data=None):
        """
        Updates values in database entries based on their key.

        Args:
            data: e.g. {"name": "schmidt", "street": "dorfstr"}. JSON formated entry with keys "name" & "street"
                        where street is the new value

        Returns: dynamic generated HTML displaying all data
        """

        self.error_message = None
        if data:
            try:
                data_dict = json.loads(data)

                if 'name' not in data_dict:
                    self.error_message = "'name' is missing."
                    rendered_html = self.render_template([], [], error=self.error_message)
                    return rendered_html
                else:
                    name_to_update = data_dict['name']
                    self.db.update(data_dict, name=name_to_update)
            except json.JSONDecodeError as e:
                self.error_message = "No valid JSON-data was given:<br>" + str(e)
                rendered_html = self.render_template([], [], error=self.error_message)
                return rendered_html
        else:
            self.error_message = "No input detected.<br>Please enter valid JSON."
            rendered_html = self.render_template([], [], error=self.error_message)
            return rendered_html

        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def delete_data(self, filter=None):
        """
        Deletes entries based on given filter or all entries.

        Args:
            filter: "Name" for to be deleted entries

        Returns: Returns to starting page
        """

        self.error_message = None
        if filter:
            self.db.delete(name=filter)
        else:
            # if no filter is given all data will be deleted
            try:
                self.db.delete()
            except Exception as e:
                self.error_message = "An error occured while deleting all data:<br>" + str(e)
        raise cherrypy.HTTPRedirect('/')

    def _copy_file(self, source_file, target_file):
        """
        Copys source file into target file.

        Args:
            source_file: filename for file to be copied
            target_file: filename for file to be copied into
        """

        with open(target_file, 'wb') as dest, open(source_file, 'rb') as src:
            dest.write(src.read())

    @cherrypy.expose
    def reset_data(self):
        """
        ONLY FOR DEVELOPMENT PURPOSES!!!
        Uses _copy_file to resorte file from file.backup.
        ONLY FOR DEVELOPMENT PURPOSES!!!
        """

        # check for backup file
        if os.path.exists(self.csv_backup):
            self._copy_file(self.csv_backup, self.csv_filename)
            return "Reset successful"
        else:
            raise cherrypy.HTTPError(400, "Backup file not found")


if __name__ == '__main__':
    csv_filename = 'some-file.csv'
    cherrypy.quickstart(TableApp(csv_filename))
