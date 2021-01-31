"""
An small example of using threads to perform queued actions

Two runners execute actions with a dummy value for a certain duration

One longpoll thread checks the status of the queue periodically
"""

import threading
import inspect
import time
from queue import Queue
from dataclasses import dataclass
from typing import List

RESET_VALUE = -180


@dataclass()
class ValueDuration:
    value: int
    duration: float


class Thread(threading.Thread):
    """
    A thread that is started on initialisation
    """

    def __init__(self, *args, **kwargs):
        super(Thread, self).__init__(*args, **kwargs)
        self.start()


current_value = 0
lock = threading.Lock()


def perform_actions(actions: List[ValueDuration], **kwargs):
    """
    Perform each action using a lock.
    Set a global (note that you may not want to do this in a production setting)
    Also print the thread calling the function and the parent caller
    """
    global current_value
    caller = inspect.stack()[1].function
    current_thread_name = threading.current_thread().name
    with lock:
        print(f"Lock acquired by {current_thread_name}:{caller}")
        print(f"Using: {kwargs}")
        for action in actions:
            current_value = action.value
            print(f"{caller} Executing {action}...")
            time.sleep(action.duration)
        print(f"{caller} releasing lock\n")


def run_seldom(actions_queue: Queue, wait_until_acquire_next_task: float = 1):
    """
    Threading target for one run mechanism that runs seldom
    """
    while not actions_queue.empty():
        value_actions = actions_queue.get()
        perform_actions(value_actions, profile_name="seldom")
        time.sleep(wait_until_acquire_next_task)


def run_often(actions_queue: Queue, wait_until_acquire_next_task: float = 0.2):
    """
    Threading target for another run mechanism that runs often
    """
    while not actions_queue.empty():
        value_actions = actions_queue.get()
        perform_actions(value_actions, profile_name="often")
        time.sleep(wait_until_acquire_next_task)


def at_least_one_remaining_runner():
    """ Runner threads should have 'runner' in the thread name """
    active_threads = threading.enumerate()
    for thread in active_threads:
        if "runner" in thread.name:
            return True
    return False


def longpoll():
    """ Periodically print the remaining actions """
    global current_value
    while at_least_one_remaining_runner():
        with lock:
            print("longpoll Acquired lock")
            print(
                f"Current val: {current_value}\nRemaining : {actions_queue.queue}")
            time.sleep(0.1)
            print("longpoll releasing lock\n")
        time.sleep(2)


if __name__ == "__main__":
    # We first create a queue where each item will be a list of
    # ValueDuration objects

    # Add some values into an actions queue.
    actions_queue = Queue()
    for lower_value in range(10, 50, 2):
        higher_value = lower_value + 5
        actions_queue.put(
            [
                ValueDuration(lower_value, 0.1),
                ValueDuration(higher_value, 0.2),
                ValueDuration(RESET_VALUE, 0.1),
            ]
        )

    # Now we make two runner threads, one running "seldom" and one "often"
    # Note that these will start upon initialisation
    runner_seldom = Thread(
        target=run_seldom, kwargs={"actions_queue": actions_queue},
        name="runner_seldom"
    )
    runner_often = Thread(
        target=run_often, kwargs={"actions_queue": actions_queue},
        name="runner_often"
    )

    # Make another polling thread to periodically print what
    # remains in the actions_queue
    pollthread = Thread(target=longpoll, name="pollthread")

    # Wait for all threads to join
    runner_seldom.join()
    runner_often.join()
    pollthread.join()
