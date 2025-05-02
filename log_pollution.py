import copy
import math
import random
from abc import ABC, abstractmethod

from mako.util import to_list

"""
Currently implemented Polluters

Incomplete Data:
    Delete...   ...random activity (DeleteActivityPolluter)
    
Incorrect Data:
    Insert...   ...alien activity (InsertAlienActivityPolluter)
                ...known activity (InsertRandomActivityPolluter)
                ...duplicate activity (InsertDuplicateActivityPolluter)
    Replace...  ...alien activity (ReplaceAlienActivityPolluter)
                ...known activity (ReplaceRandomActivityPolluter)
                ...duplicate activity (ReplaceDuplicateActivityPolluter)
"""

class LogPolluter(ABC):
    @abstractmethod
    def pollute(self, log):
        pass

    def get_properties(self):
        properties = {key: value for key, value in self.__dict__.items() if not key.startswith('__') and not callable(key)}
        properties["pollution_pattern"] = self.__class__.__name__
        return properties


class InsertAlienActivityPolluter(LogPolluter):
    """
    Insert a selected percentage of alien activities in the log

    Example: A B C D E --> A B C D fchildsf3d1 E
    """
    def __init__(self, percentage):
        self.percentage = percentage

    def pollute(self, log):
        log_copy = copy.deepcopy(log)
        number_of_events = sum([len(tr) for tr in log])

        to_duplicate = math.ceil(number_of_events * self.percentage)

        for _ in range (to_duplicate):
            tr = random.choice(log_copy)
            to_insert = random.randint(0, len(tr)-1)
            tr.insert(to_insert+1, tr[to_duplicate])
            tr[to_duplicate+1]["concept:name"] = str(random.getrandbits(128))

        return log_copy


class InsertDuplicateActivityPolluter(LogPolluter):
    """
    Duplicates a selected percentage of activities in the log

    Example: A B C D E --> A B C D D E
    """
    def __init__(self, percentage):
        self.percentage = percentage

    def pollute(self, log):
        log_copy = copy.deepcopy(log)
        number_of_events = sum([len(tr) for tr in log])

        to_duplicate = math.ceil(number_of_events * self.percentage)

        for _ in range (to_duplicate):
            tr = random.choice(log_copy)
            to_insert = random.randint(0, len(tr)-1)
            tr.insert(to_insert+1, tr[to_insert])

        return log_copy


class InsertRandomActivityPolluter(LogPolluter):
    """
    Inserts a selected percentage of random log-based activities in the log

    Example: A B C D E --> A B C D {A/B/C/E} E
    """
    def __init__(self, percentage):
        self.percentage = percentage

    def pollute(self, log):
        log_copy = copy.deepcopy(log)
        number_of_events = sum([len(tr) for tr in log])

        to_duplicate = math.ceil(number_of_events * self.percentage)
        log_activities = set()
        for tr in log_copy:
            for e in tr:
                log_activities.add(e["concept:name"])

        for _ in range (to_duplicate):
            tr = random.choice(log_copy)
            trace_to_duplicate = random.randint(0, len(tr)-1)
            tr.insert(trace_to_duplicate+1, tr[trace_to_duplicate])
            tr[trace_to_duplicate+1]["concept:name"] = random.choice(list(log_activities))

        return log_copy


class DeleteActivityPolluter(LogPolluter):
    """
    Deletes a selected percentage of activities in the log

    Example: A B C D E --> A B C E
    """
    def __init__(self, percentage):
        self.percentage = percentage

    def pollute(self, log):
        log_copy = copy.deepcopy(log)
        number_of_events = sum([len(tr) for tr in log])

        to_delete = math.ceil(number_of_events * self.percentage)

        for _ in range (to_delete):
            tr = random.choice(log_copy)
            tr.pop(random.randint(0,len(tr)-1))

        return log_copy


class ReplaceAlienActivityPolluter(LogPolluter):
    """
    Replaces a selected percentage of activities in the log with random unique activities

    Example: A B C D E --> A B C xhfuej32 E
    """
    def __init__(self, percentage):
        self.percentage = percentage

    def pollute(self, log):
        log_copy = copy.deepcopy(log)
        number_of_events = sum([len(tr) for tr in log])

        to_duplicate = math.ceil(number_of_events * self.percentage)

        for _ in range (to_duplicate):
            tr = random.choice(log_copy)

            to_replace = random.randint(0, len(tr)-1)
            tr[to_replace]["concept:name"] = str(random.getrandbits(128))

        return log_copy


class ReplaceRandomActivityPolluter(LogPolluter):
    """
    Replaces a selected percentage of activities in the log with random unique activities

    Example: A B C D E --> A B C {A/B/C/D/E} E
    """

    def __init__(self, percentage):
        self.percentage = percentage

    def pollute(self, log):
        log_copy = copy.deepcopy(log)
        number_of_events = sum([len(tr) for tr in log])

        to_duplicate = math.ceil(number_of_events * self.percentage)
        log_activities = set()
        for tr in log_copy:
            for e in tr:
                log_activities.add(e["concept:name"])

        for _ in range(to_duplicate):
            tr = random.choice(log_copy)

            to_replace = random.randint(0, len(tr) - 1)
            tr[to_replace]["concept:name"] = random.choice(list(log_activities))

        return log_copy


class ReplaceDuplicateActivityPolluter(LogPolluter):
    """
    Replaces a selected percentage of activities in the log with random unique activities

    Example: A B C D E --> A B C C E
    """

    def __init__(self, percentage):
        self.percentage = percentage

    def pollute(self, log):
        log_copy = copy.deepcopy(log)
        number_of_events = sum([len(tr) for tr in log])

        to_duplicate = math.ceil(number_of_events * self.percentage)

        for _ in range(to_duplicate):
            tr = random.choice(log_copy)
            to_duplicate = random.randint(1, len(tr) - 1)
            tr[to_duplicate]["concept:name"] = tr[to_duplicate - 1]["concept:name"]

        return log_copy


def create_pollution_testbed():
    percentages = [0.10, 0.20, 0.30, 0.40, 0.50]

    insert_random_activity_polluters = [InsertRandomActivityPolluter(x) for x in percentages]
    insert_duplicate_activity_polluters = [InsertDuplicateActivityPolluter(x) for x in percentages]
    insert_alien_activity_polluters = [InsertAlienActivityPolluter(x) for x in percentages]

    replace_random_activity_polluters = [ReplaceRandomActivityPolluter(x) for x in percentages]
    replace_duplicate_activity_polluters = [ReplaceDuplicateActivityPolluter(x) for x in percentages]
    replace_alien_activity_polluters = [ReplaceAlienActivityPolluter(x) for x in percentages]

    delete_random_activity_polluters = [DeleteActivityPolluter(x) for x in percentages]

    return (insert_random_activity_polluters +
                 insert_duplicate_activity_polluters +
                 insert_alien_activity_polluters +
                 replace_random_activity_polluters +
                 replace_duplicate_activity_polluters +
                 replace_alien_activity_polluters +
                 delete_random_activity_polluters)