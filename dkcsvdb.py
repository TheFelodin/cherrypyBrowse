from operator import eq, ne

def connect(filename):
    fp = open(filename, mode="r+")
    return Dkcsvdb(fp)


class Dkcsvdb:
    """
    A class for managing CSV data in a file.
    """

    def __init__(self, fp):
        self.fp = fp

    def _read_data(self):
        """
        Read the data from the file.

        Returns:
            The headers and a list with the entries.
        """

        self.fp.seek(0)

        # Reads first line and splits by comma to get headers
        headers = self.fp.readline().strip().rsplit(',')
        resultlist = []

        # Reads followings lines to get entries split by comma
        for line in self.fp:
            line = line.rstrip()
            values = line.split(",")
            kv = dict(zip(headers, values))
            resultlist.append(kv)

        # Returns headers and data
        return headers, resultlist

    def _write_data(self, headers, data):
        """
        Write Data to the file.

        Args:
            data: List of entries
        """

        self.fp.seek(0)

        # Writes headers into file
        self.fp.write(",".join(headers) + '\n')

        # Writes entries
        for row in data:
            self.fp.write(','.join([str(row[h]) for h in headers]) + '\n')

        # Sets end of file to current position
        self.fp.truncate()

    def _filter_data(self, resultlist, foretoken, **filters):
        """
        Sorts through the given data by filter.

        Args:
            **filters: Keys searched for
            foretoken: True or False to indicate what should be returned. The list with the filter or without.

        Returns:
            List of entries depending on filter and foretoken.

        """

        # If foretoken is True a list of entries with the given key is created, if not every other data is selected
        cmp_op = eq if foretoken else ne
        for key, value in filters.items():
            resultlist = [data for data in resultlist if cmp_op(data[key], value)]
        return resultlist

    def fetch(self, **filters):
        """
        Retrieves entries based on the given item. Or all if nothing is given.

        Args:
            **filters: Items to search for. If none is given, all data will be returned.

        Returns:
            A list of entries.
        """

        # Reads headers and data from file
        headers, resultlist = self._read_data()

        # Create a list depending on given filter
        resultlist = self._filter_data(resultlist, foretoken=True, **filters)

        # Returns list
        return resultlist

    def insert(self, data):
        """
        Insert a new data.

        Args:
            data: An data to be inserted into the data.
        """

        # Reads headers and data from file
        headers, resultlist = self._read_data()

        # Adds the given data to the data
        resultlist.append(data)

        # Write the updated data to file
        self._write_data(headers, resultlist)

    def update(self, new_data, **filters):
        """
        Update records in the data based on the search criteria and new values.

        Args:
            filters (dict): A dictionary specifying the criteria to search for records.
            new_data (dict): A dictionary specifying the new values to update in matching records.

        Returns:
            None
        """

        # Reads headers and data from file
        headers, resultlist = self._read_data()

        # Sort and filter the resultlist based on the search criteria
        filtered_resultlist = self._filter_data(resultlist, foretoken=True, **filters)

        # Update matching records with new values
        for data in filtered_resultlist:
            data.update(new_data)

        # Write the updated data to file
        self._write_data(headers, resultlist)

    def delete(self, **filters):
        """
        Delete data based on given statement.

        Args:
            **filters: Detail of the data to be deleted. If none is provided, all data is deleted.
        """

        # Reads headers and data from file
        headers, resultlist = self._read_data()
        if filters:
            # Creates a list with all the entries not having the filter key
            resultlist = self._filter_data(resultlist, foretoken=False, **filters)
        else:
            resultlist = []

        # Write the updated data to file
        self._write_data(headers, resultlist)
