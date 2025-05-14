import copy
import math
import random
import numpy as np
import datetime as dt
from abc import ABC, abstractmethod
from copy import deepcopy
from collections import defaultdict

from mako.util import to_list
from pm4py.objects.log.obj import EventLog
from pm4py.statistics.attributes.log import get as attributes_get

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
                
    Timestamp... ...delayed event logging     (DelayingEventLoggingPolluter)
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
    def __init__(self, percentage, alien_activity_nr):
        self.percentage = percentage
        self.alien_activity_nr = alien_activity_nr

    # I (Yannis) modified this polluter to take a number of alien activities instead of generating a different activity for each event (which really messed up the event log too much)
    # if you do not give in a number of alien activities, this number will be set to the number of events to insert and an activity label will be randomly drawn from this list (slightly different behaviour than original)
    def pollute(self, log):
        log_copy = copy.deepcopy(log)
        number_of_events = sum([len(tr) for tr in log])
        if self.alien_activity_nr is None:
            self.alien_activity_nr = number_of_events
        alien_activities = []

        to_duplicate = math.ceil(number_of_events * self.percentage)

        for _ in range(self.alien_activity_nr):
            alien_activities.append(str(random.getrandbits(128)))

        for _ in range (to_duplicate):
            tr = random.choice(log_copy)
            to_insert = random.randint(0, len(tr)-1)
            new_event = copy.deepcopy(tr[to_insert])
            new_event['concept:name'] =random.choice(alien_activities)
            tr.insert(to_insert+1, new_event) # the deep copy is there to solve an issue that duplicated the inserted activity

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
            log.append(random.choice(log_copy))

        return log_copy


class ReplaceAlienActivityPolluter(LogPolluter):
    """
    Replaces a selected percentage of activities in the log with random unique activities

    Example: A B C D E --> A B C xhfuej32 E
    """
    def __init__(self, percentage, alien_activity_nr):
        self.percentage = percentage
        self.alien_activity_nr = alien_activity_nr

    # I (Yannis) modified this polluter to take a number of alien activities instead of generating a different activity for each event (which really messed up the event log too much)
    # if you do not give in a number of alien activities, this number will be set to the number of events to insert and an activity label will be randomly drawn from this list (slightly different behaviour than original)
    def pollute(self, log):
        log_copy = copy.deepcopy(log)
        number_of_events = sum([len(tr) for tr in log])
        if self.alien_activity_nr is None:
            self.alien_activity_nr = number_of_events
        alien_activities = []

        to_duplicate = math.ceil(number_of_events * self.percentage)

        for _ in range(self.alien_activity_nr):
            alien_activities.append(str(random.getrandbits(128)))

        for _ in range (to_duplicate):
            tr = random.choice(log_copy)

            to_replace = random.randint(0, len(tr)-1)
            tr[to_replace]["concept:name"] = random.choice(alien_activities)

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

class DelayedEventLoggingPolluter(LogPolluter):
    """
    Replaces the timestamp of an event with a later timestamp by introducing a delay sampled from a gamma distribution

    Example: 12:34:56 -> 12:34:56 + 14 min = 12:48:56
    """

    def __init__(self, percentage, distribution='gamma', parameters={'shape': 2, 'scale': 2}, mean_delay= 30):
        self.percentage = percentage
        self.distribution = distribution
        self.parameters = parameters
        self.mean_delay = mean_delay

    def pollute(self, log):
        log_copy = deepcopy(log)
        number_of_events = sum([len(tr) for tr in log])

        to_pollute = math.ceil(number_of_events * self.percentage)

        # compute a rescaling factor to to get a delay with a mean = mean_delay based on a sampling of the gamma distribution
        rescale_factor = self.mean_delay / (self.parameters['shape'] * self.parameters['scale'])

        for _ in range(to_pollute):
            tr = random.choice(log_copy)

            to_replace = random.randint(0, len(tr) - 1)
            tr[to_replace]["time:timestamp"] += dt.timedelta(minutes=np.random.gamma(shape=self.parameters['shape']) * rescale_factor)

        # Sort each trace by timestamp as order of events may have shifted
        for i, tr in enumerate(log_copy):
            sorted_trace = sorted(tr, key=lambda event: event['time:timestamp'])
            log_copy[i][:] = sorted_trace

        return log_copy

class AggregatedEventLoggingPolluter(LogPolluter):
    """
    Replaces the timestamp of an event with a more coarse-grained timestamp

    Example: 12:34:56 -> 12:00:00
    """

    # supported values for target_precision: day, hour, quarter, minute, second
    def __init__(self, percentage, target_precision='hour'):
        self.percentage = percentage
        self.target_precision = target_precision

    # this function assumes that target_precision is more coarse than current precision
    def pollute(self, log):
        log_copy = deepcopy(log)
        number_of_events = sum([len(tr) for tr in log])

        to_pollute = math.ceil(number_of_events * self.percentage)

        for _ in range(to_pollute):
            tr = random.choice(log_copy)

            to_replace = random.randint(0, len(tr) - 1)
            #print(tr[to_replace])

            if self.target_precision == 'second':
                tr[to_replace]["time:timestamp"].replace(microsecond=0)
            elif self.target_precision == 'minute':
                tr[to_replace]["time:timestamp"].replace(second=0, microsecond=0)
            elif self.target_precision == 'quarter':
                tr[to_replace]["time:timestamp"].replace(minute=(tr[to_replace]["time:timestamp"]//15)*15, second=0, microsecond=0)
            elif self.target_precision == 'hour':
                tr[to_replace]["time:timestamp"].replace(minute=0, second=0, microsecond=0)
            elif self.target_precision == 'day':
                tr[to_replace]["time:timestamp"].replace(hour=0, minute=0, second=0, microsecond=0)
            #print(tr[to_replace])

        for i, tr in enumerate(log_copy):
            # Group events by timestamp
            timestamp_groups = defaultdict(list)
            for event in tr:
                timestamp_groups[event['time:timestamp']].append(event)

            # Sort timestamps to maintain overall trace order
            sorted_timestamps = sorted(timestamp_groups.keys())

            # Build new trace by shuffling events in each group
            new_tr = []
            for ts in sorted_timestamps:
                group = timestamp_groups[ts]
                random.shuffle(group)  # Shuffle in-place
                new_tr.extend(group)

            log_copy[i] = new_tr

        return log_copy

class ImpreciseActivityPolluter(LogPolluter):
    """
    Replaces the activity name of an event with a more fine-grained one

    Example: A -> A_2
    """
    def __init__(self, percentage, imprecision_levels=1):
        self.imprecision_levels = imprecision_levels # number of levels of precision to add
        self.percentage = percentage # percentage of activities impacted

    def pollute(self, log):
        log_copy = deepcopy(log)

        activities_list = list(attributes_get.get_attribute_values(log, "concept:name").keys())

        number_of_activities = math.ceil(len(activities_list) * self.percentage)
        to_pollute = activities_list[:number_of_activities]
        #print(activities_list, number_of_activities)

        for i, tr in enumerate(log_copy):
            #print(tr)
            for j, event in enumerate(tr):
                if tr[j]["concept:name"] in to_pollute:
                    #print(tr[j]["concept:name"])
                    for _ in range(self.imprecision_levels):
                        tr[j]["concept:name"] += '_' + str(random.randint(1,5))
                    #print(tr[j]["concept:name"])

            #print(tr)

        return log_copy

def create_pollution_testbed(percentages=[0.10, 0.20, 0.30, 0.40, 0.50]):

    #insert_random_activity_polluters = [InsertRandomActivityPolluter(x) for x in percentages]
    #insert_duplicate_activity_polluters = [InsertDuplicateActivityPolluter(x) for x in percentages]
    insert_alien_activity_polluters = [InsertAlienActivityPolluter(x, 4) for x in percentages]

    #replace_random_activity_polluters = [ReplaceRandomActivityPolluter(x) for x in percentages]
    replace_duplicate_activity_polluters = [ReplaceDuplicateActivityPolluter(x) for x in percentages]
    #replace_alien_activity_polluters = [ReplaceAlienActivityPolluter(x) for x in percentages]

    #delete_random_activity_polluters = [DeleteActivityPolluter(x) for x in percentages]

    #insert_duplicate_trace_polluters = [InsertDuplicateTracePolluter(x) for x in percentages]
    #delete_random_trace_polluters = [DeleteTracePolluter(x) for x in percentages]

    #delay_event_logging_polluters = [DelayedEventLoggingPolluter(x, mean_delay=120) for x in percentages]
    aggregate_timestamp_polluters = [AggregatedEventLoggingPolluter(percentage=x, target_precision='hour') for x in percentages]
    #imprecise_activity_polluters = [ImpreciseActivityPolluter(percentage=x) for x in percentages]

    all_polluters = [insert_alien_activity_polluters, replace_duplicate_activity_polluters, aggregate_timestamp_polluters]
            #[insert_random_activity_polluters, insert_duplicate_activity_polluters, insert_alien_activity_polluters,
            #replace_random_activity_polluters, replace_duplicate_activity_polluters, replace_alien_activity_polluters,
            #delete_random_activity_polluters, insert_duplicate_trace_polluters, delete_random_trace_polluters,
            #delay_event_logging_polluters, aggregate_timestamp_polluters, imprecise_activity_polluters]

    return [polluter for polluter_group in all_polluters for polluter in polluter_group]