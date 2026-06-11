"""
Task scheduler module
"""
from abc import ABC, abstractmethod
import datetime
import logging
import threading
import time
from typing import Any, Callable, Optional

from bah.exceptions import BAHException


class Task:
    """
    Class representing a task
    """

    def __init__(
            self,
            name: str,
            run_every: int,
            call: Callable,
            callback: Optional[Callable] = None,
            **kwargs: Any
    ) -> None:
        self._last_run: Optional[datetime.datetime] = None
        self._run_every = run_every
        self._call = call
        self._callback = callback
        self._on_exception: Optional[Callable] = kwargs.pop('on_exception', None)
        self._name = name

    def __str__(self) -> str:
        return self._name

    def is_due(self) -> bool:
        """
        Check if this task is due to be executed

        :return:
        """
        return (self._last_run is None or
                datetime.datetime.now() - self._last_run >= datetime.timedelta(seconds=self._run_every))

    def start(self) -> None:
        """
        Start the task

        :return:
        """
        logging.info('Starting task: %s', self._name)
        self._last_run = datetime.datetime.now()
        try:
            result = self._call()
            if self._callback:
                self._callback(result)
        except BAHException as error:
            if self._on_exception:
                logging.warning('Exception raised while executing task: %s', str(error))
                self._on_exception(error)
            else:
                logging.error('Exception raised while executing task: %s', str(error))
                raise


class TaskScheduler(ABC):
    """
    Implements the scheduling of tasks
    """

    def __init__(self) -> None:
        self._background_thread: threading.Thread = threading.Thread(target=self.run)

    @property
    @abstractmethod
    def tasks(self) -> list[Task]:
        """
        List of tasks to schedule

        :return:
        """

    def run(self) -> None:
        """
        Main run method. The method iterates through the tasks and executes them if they are due

        :return:
        """
        while True:
            for task in self.tasks:
                logging.debug('Checking task: %s', str(task))
                if task.is_due():
                    task.start()
            time.sleep(0.1)

    def run_async(self) -> None:
        """
        Run the main function in a background thread

        :return:
        """
        self._background_thread.start()
