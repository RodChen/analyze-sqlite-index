import apsw
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        usage='Analyze a SQLite database to list \n'
              '1. used index\n'
              '2. index not in use\n'
              '3. help find missing index',
    )
    parser.add_argument('db_file', help='SQLite database file')
    parser.add_argument('query_file', help='a text file containing SQL queries'
                                           ' in format of one line one query')
    args = parser.parse_args()
    conn = apsw.Connection(args.db_file)
    cursor = conn.cursor()
    queries = [line.rstrip('\n') for line in open(args.query_file)]

    scan = {}  # {"SQL query": "SCAN TABLE ..."}
    search = {}  # {"SQL query": "SEARCH TABLE..."}
    all_index = {}  # {index1: used_times}
    for q in queries:
        try:
            res = cursor.execute('EXPLAIN QUERY PLAN ' + q)
        except Exception as e:
            print('ERROR in running query=%s' % q)
            raise e
        row = next(res)
        if row[3].startswith('SCAN'):
            scan[q] = row[3]
        elif row[3].startswith('SEARCH'):
            search[q] = row[3]

    indices = cursor.execute("SELECT name FROM sqlite_master WHERE type = "
                             "'index' AND name NOT LIKE '%_autoindex_%'")
    for i in indices:
        all_index[i[0]] = 0
    for result in search.values():
        parts = result.split(' ')
        index_pos = 0
        for i, value in enumerate(parts):
            if value == 'INDEX':
                index_pos = i + 1
        used_index = parts[index_pos]
        # don't count sqlite auto index, only index created by us
        if all_index.get(used_index) is not None:
            all_index[used_index] += 1
    print('{!s:<40}|{!s:<20}'.format('Used indices', 'How many queries use it'))
    print('-'*61)
    for index, count in all_index.items():
        if count > 0:
            print('{!s:<40}|{!s:^20}'.format(index, count))
    print('-'*61)
    print('NOT USED INDEX: ')
    for index, count in all_index.items():
        if count == 0:
            print(index)

    print('-'*61)
    print('MISSING index: Examine following queries involving SCAN TABLE')
    for k, v in scan.items():
        print(' ')
        print('EXPLAIN QUERY PLAN ' + k)
        print(v)

    print('-'*61)
    print('Queries involving SEARCH TABLE:')
    for k, v in search.items():
        print(' ')
        print('EXPLAIN QUERY PLAN ' + k)
        print(v)
