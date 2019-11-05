from pprint import pformat
from htp import celery as app
from celery.events import EventReceiver
from celery.events.snapshot import Polaroid
from kombu import Connection as BrokerConnection


def my_monitor():
    connection = BrokerConnection('redis://localhost')

    def on_event(event):
        print(f"EVENT HAPPENED: {event},")

    def on_task_failed(event):
        exception = event['exception']
        print(f"TASK FAILED! {event} EXCEPTION: {exception},")

    while True:
        try:
            with connection as conn:
                recv = EventReceiver(
                    conn,
                    handlers={
                        'task-failed' : on_task_failed,
                        'task-succeeded' : on_event,
                        'task-sent' : on_event,
                        'task-received' : on_event,
                        'task-revoked' : on_event,
                        'task-started' : on_event,
                        })
                recv.capture(limit=None, timeout=None)
        except (KeyboardInterrupt, SystemExit):
            print("EXCEPTION KEYBOARD INTERRUPT")
            sys.exit()


class DumpCam(Polaroid):
    clear_after = True  # clear after flush (incl, state.event_count).

    def on_shutter(self, state):
        if not state.event_count:
            # No new events since last snapshot.
            return
        print('Workers: {0}'.format(pformat(state.workers, indent=4)))
        print('Tasks: {0}'.format(pformat(state.tasks, indent=4)))
        print('Total: {0.event_count} events, {0.task_count} tasks'.format(
            state))


def main(app=app, freq=1.0):
    state = app.events.State()
    with app.connection() as connection:
        recv = app.events.Receiver(connection, handlers={'*': state.event})
        with DumpCam(state, freq=freq):
            recv.capture(limit=None, timeout=None)
