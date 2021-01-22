# -*- coding: utf-8 -*-
import sys
import click

from wbia.dtool.copy_sqlite_to_postgres import (
    SqliteDatabaseInfo,
    PostgresDatabaseInfo,
    compare_databases,
)


@click.command()
@click.option(
    '--db-dir',
    multiple=True,
    help='SQLite databases location',
)
@click.option(
    '--sqlite-uri',
    multiple=True,
    help='SQLite database URI (e.g. sqlite:////path.sqlite3)',
)
@click.option(
    '--pg-uri',
    multiple=True,
    help='Postgres connection URI (e.g. postgresql://user:pass@host)',
)
def main(db_dir, sqlite_uri, pg_uri):
    if len(db_dir) + len(sqlite_uri) + len(pg_uri) != 2:
        raise click.BadParameter('exactly 2 db_dir or sqlite_uri or pg_uri must be given')
    db_infos = []
    for db_dir_ in db_dir:
        db_infos.append(SqliteDatabaseInfo(db_dir_))
    for sqlite_uri_ in sqlite_uri:
        db_infos.append(SqliteDatabaseInfo(sqlite_uri_))
    for pg_uri_ in pg_uri:
        db_infos.append(PostgresDatabaseInfo(pg_uri_))
    exact = not (sqlite_uri and pg_uri)
    differences = compare_databases(*db_infos, exact=exact)
    if differences:
        click.echo(f'Databases {db_infos[0]} and {db_infos[1]} are different:')
        for line in differences:
            click.echo(line)
        sys.exit(1)
    else:
        click.echo(f'Databases {db_infos[0]} and {db_infos[1]} are the same')


if __name__ == '__main__':
    main()
