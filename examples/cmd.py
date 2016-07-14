from schema_sugar.client.client import RestClient
from schema_sugar.client.parser import run_cmds
from schema_sugar.client.support.flask import parse_rule


def main():
    client = RestClient(parse_rule)
    print run_cmds(client)

main()