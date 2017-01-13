import json
import os
import signal

import click
import stomp

from minecart.packager import create_archive, upload, docset, notify


@click.group()
def main():
    pass


@main.command()
@click.option('--broker-host', default='localhost')
@click.option('--broker-port', default=61613)
@click.option('--api-host', default='localhost')
@click.option('--api-port', default=80)
@click.option('--repo-host', default='locahost')
@click.option('--repo-port', default=8080)
@click.option('--queue', default='/queue/api')
def run(broker_host, broker_port, api_host, api_port, repo_host, repo_port,
        queue):
    conn = stomp.Connection([(broker_host, broker_port)])
    conn.set_listener('archiver', ApiListener())
    conn.start()
    conn.connect(wait=True)
    conn.subscribe(queue, 1)

    while True:
        signal.pause()


class ApiListener(stomp.ConnectionListener):
    def on_message(self, headers, message):
        handle_message(message)


def handle_message(message):
    msg = json.loads(message)
    docs = docset(msg['docset'])
    arxv = create_archive(docs)
    try:
        package = upload(arxv)
    except Exception:
        raise
    finally:
        os.remove(arxv)
    notify(package)
