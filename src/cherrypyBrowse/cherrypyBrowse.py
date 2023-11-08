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

    def render_template(self, headers, entries, filters=None, error=None):
        """
        Creates a hmtl file displaing data in a table.

        Args:
            headers: Table headers
            entries: Data shown in the table
            filters: Inputfield content
            error: Error message to display

        Returns: dynamic generated HTML
        """

        template = self.template_env.get_template('table_template.html')
        return template.render(headers=headers, entries=entries, filters=filters, error=error)

    @cherrypy.expose
    def index(self, **filters):
        """
        Collects data from file

        Returns: dynamic generated HTML displaying selected entries or error message
        """
        print("AAAAAAAAA:", cherrypy.request.request_line, "BBBBBBBBBBBBB")
        # if cherrypy.request.request_line.endswith("?"):
        #     raise cherrypy.HTTPRedirect('/')

        # fetches data by filter or all if no filter is given
        error_message = None
        try:
            entries = self.db.fetch(**filters)

        except KeyError:
            error_message = "Invalid filter given.<br>Please check \"Input Examples\""
            entries = self.db.fetch()

        # creates HTML with selected entries
        if entries:
            rendered_html = self.render_template(entries[0].keys(), entries, error=error_message)
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

        if data:
            try:
                # convert input to JSON
                data_dict = json.loads(data)
                self.db.insert(data_dict)

            # if no valid JSON string was given, return error
            except json.JSONDecodeError as e:
                error_message = "No valid JSON-data was given:<br>" + str(e)
                rendered_html = self.render_template([], [], error=error_message)
                return rendered_html
        else:
            error_message = "No input detected.<br>Please enter valid JSON."
            rendered_html = self.render_template([], [], error=error_message)
            return rendered_html

        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def update_data(self, new_data):
        """
        Updates values in database entries based on their key.

        Args:
            new_data: e.g. new_data={"key_for_value_to cange": "new_value"}, **{"key_to_search_by": "value_to_search_by"}

        Returns: dynamic generated HTML displaying all data
        """

        if new_data:
            try:
                data_dict = json.loads(new_data)
                new_data_formated = f'new_data={new_data[0]}, \*\*'
                if 'name' not in data_dict or 'street' not in data_dict:
                    error_message = "'key' is missing."
                    rendered_html = self.render_template([], [], error=error_message)
                    return rendered_html
                elif "name" in data_dict:
                    name_to_update = data_dict['name']
                    self.db.update(data_dict, name=name_to_update)
                elif "street" in data_dict:
                    street_to_update = data_dict['street']
                    self.db.update(data_dict, street=street_to_update)
            except json.JSONDecodeError as e:
                error_message = "No valid JSON-data was given:<br>" + str(e)
                rendered_html = self.render_template([], [], error=error_message)
                return rendered_html
        else:
            error_message = "No input detected.<br>Please check \"Input Examples\""
            rendered_html = self.render_template([], [], error=error_message)
            return rendered_html

        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def delete_data(self, **filters):
        """
        Deletes entries based on given filter or all entries.

        Returns: Returns to starting page
        """
        try:
            self.db.delete(**filters)
        except KeyError:
            error_message = "Invalid filter given.<br>Please check \"Input Examples\""
            return self.render_template([], [], filters=filters, error=error_message)

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
