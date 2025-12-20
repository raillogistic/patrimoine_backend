import re
from django.db.backends.oracle import base, features
from django.db.backends.oracle.operations import DatabaseOperations
from django.utils.asyncio import async_unsafe


def transform_sql(limit=0, offset=0):
    if offset > 0 and limit > 0:
        return f"L{limit}:O{offset}"
    if limit > 0:
        return ("WHERE ROWNUM <= %d " % limit)

    # return (f"WHERE ROWNUM BETWEEN  {fetch} and {fetch+offset} ")
    # if offset is None or offset == 0:
    #     return ("WHERE ROWNUM <= %d " % fetch)
    # if offset > 0:
    #     res = fetch+offset
    #     return ("WHERE ROWNUM <= %d " % res)
    # return ("WHERE ROWNUM <= %d " % fetch) if fetch > 1 else None


class MyDataBaseOperation(DatabaseOperations):
    def limit_offset_sql(self, low_mark, high_mark):
        fetch, offset = self._get_limit_offset_params(low_mark, high_mark)
        # print(fetch, offset)
        return " ".join(
            sql
            for sql in (
                # ("WHERE ROWNUM > %d" % offset) if offset else None,
                # ("and rownum <= %d " %
                #  fetch) if fetch > 1 and "where" in sql.lower() else None,
                transform_sql(fetch, offset),
            )
            if sql
        )


def replace_second_occurrence(string, old_word, new_word):
    first_index = string.find(old_word)  # find the first occurrence
    # find the second occurrence
    second_index = string.find(old_word, first_index + 1)
    if second_index == -1:  # check if the second occurrence exists
        return string  # return the original string
    # slice the string before the second occurrence
    before = string[:second_index]
    second = string[second_index:second_index +
                    len(old_word)]  # slice the second occurrence
    # slice the string after the second occurrence
    after = string[second_index + len(old_word):]
    # replace the second occurrence with the new word
    second = second.replace(old_word, new_word, 1)
    return before + second + after


class DatabaseFeatures(features.DatabaseFeatures):
    minimum_database_version = (11,)


def changeOrderBy(query):
    pattern = r'ORDER BY "[^"]*"\."[^\s"]+" ASC'
    matches = re.findall(pattern, query)
    if len(matches) > 0:
        query = f'{query.replace(matches[0], "")} {matches[0]}'

    pattern = r'ORDER BY "[^"]*"\."[^\s"]+" DESC'
    matches = re.findall(pattern, query)
    if len(matches) > 0:
        query = f'{query.replace(matches[0], "")} {matches[0]}'
    return query


def reform_query(query):
    # when looking for one row, change the where to AND since where is already written by rownum>limit

    count = len(re.findall('(?={})'.format(re.escape("WHERE")), query))
    if count == 2:
        query = replace_second_occurrence(query, "WHERE", "AND", )
    # move ORDER BY to the end of query
    query = changeOrderBy(query)

    return query
    # pattern = r'ORDER BY "[^"]*"\."[^\s"]+" DESC'
    # matches = re.findall(pattern, query)
    # print(matches)
    # if len(matches) > 0:
    #     query = f'{query.replace(matches[0], "")} {matches[0]}'


def find_numbers(text):
    pattern = r'L(\d+):O(\d+)'
    match = re.search(pattern, text)
    if match:
        l_number = int(match.group(1))
        o_number = int(match.group(2))
        return l_number, o_number
    else:
        return None


def reform_offset(query):
    res = find_numbers(query)
    print(res)
    if res is None:
        return query

    limit, offset = res
    if limit and offset:
        query = f"""SELECT * FROM
        (
            {query.replace(f'L{limit}:O{offset}','').replace('FROM',',rownum as rn FROM ')}
        )
        WHERE rn BETWEEN {offset} and {limit+offset}
        
         """
    return query


class MyFormatStylePlaceholderCursor(base.FormatStylePlaceholderCursor):
    def execute(self, query, params=None):

        # print("xxxxxxxxxxxx", query)
        query = reform_query(query)
        query = reform_offset(query)
        print(query, find_numbers(query))
        query, params = self._fix_for_params(
            query, params, unify_by_values=True)

        self._guess_input_sizes([params])
        with base.wrap_oracle_errors():
            return self.cursor.execute(query, self._param_generator(params))


class DatabaseWrapper(base.DatabaseWrapper):
    features_class = DatabaseFeatures
    ops_class = MyDataBaseOperation

    @async_unsafe
    def create_cursor(self, name=None):

        return MyFormatStylePlaceholderCursor(self.connection)
