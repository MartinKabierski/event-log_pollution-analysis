import copy
import math
import random
from abc import ABC, abstractmethod

from mako.util import to_list
from pm4py.objects.log.obj import EventLog

"""
Currently implemented Polluters

Incomplete Data:
    Delete...   ...random activity      (DeleteActivityPolluter)
                ...random trace         (DeleteTracePolluter)
    
Incorrect Data:
    Insert...   ...alien activity       (InsertAlienActivityPolluter)
                ...known activity       (InsertRandomActivityPolluter)
                ...duplicate activity   (InsertDuplicateActivityPolluter)
                ...duplicate trace      (InsertDuplicateTracePolluter)
    Replace...  ...alien activity       (ReplaceAlienActivityPolluter)
                ...known activity       (ReplaceRandomActivityPolluter)
                ...duplicate activity   (ReplaceDuplicateActivityPolluter)
                ...duplicate trace      (ReplaceDuplicateTracePolluter)
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
            tr.insert(to_insert+1, tr[to_insert])
            tr[to_insert+1]["concept:name"] = str(random.getrandbits(128))

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
            to_delete = random.randint(0,len(tr)-1)
            tr = tr[:to_delete] + tr[to_delete+1:]
            #tr._list.pop(to_delete)
            #tr.pop()

        return log_copy


class DeleteTracePolluter(LogPolluter):
    """
    Deletes a selected percentage of traces in the log
    Example: L={t_1, t_2, t_3, t_4} --> L={t_1, t_2, t_4}
    """
    def __init__(self, percentage):
        self.percentage = percentage

    def pollute(self, log):
        log_copy = copy.deepcopy(log)
        number_of_traces = len(log)

        to_delete = math.ceil(number_of_traces * self.percentage)

        for _ in range (to_delete):
            selected_trace = random.randint(0, len(log_copy)-1)
            #del log_copy[selected_trace:selected_trace+1]
            #log_copy = log_copy[:selected_trace] + log_copy[selected_trace+1:]
            new_log = EventLog(log_copy[:selected_trace])
            new_log.append(log_copy[selected_trace+1:])
            log_copy = new_log
            #log.pop(random.choice(log_copy))

        return log_copy


class InsertDuplicateTracePolluter(LogPolluter):
    """
    Insert a selected percentage of duplicate traces in the log
    Example: L={t_1, t_2, t_3, t_4} --> L={t_1, t_2, t_3, t_3, t_4}
    """
    def __init__(self, percentage):
        self.percentage = percentage

    def pollute(self, log):
        log_copy = copy.deepcopy(log)
        number_of_traces = len(log)

        to_insert = math.ceil(number_of_traces * self.percentage)

        for _ in range (to_insert):
            log_copy.append(random.choice(log_copy))

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
            to_duplicate = random.randint(0, len(tr) - 1)
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

    insert_duplicate_trace_polluters = [InsertDuplicateTracePolluter(x) for x in percentages]
    delete_random_trace_polluters = [DeleteTracePolluter(x) for x in percentages]

    return (insert_random_activity_polluters +
                 insert_duplicate_activity_polluters +
                 insert_alien_activity_polluters +
                 replace_random_activity_polluters +
                 replace_duplicate_activity_polluters +
                 replace_alien_activity_polluters +
                 delete_random_activity_polluters +
                 insert_duplicate_trace_polluters +
                 delete_random_trace_polluters
            )