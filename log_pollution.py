import copy
import math
import os
import random
import numpy as np
import datetime as dt
from abc import ABC, abstractmethod
from copy import deepcopy
from collections import defaultdict
from datetime import timedelta


import pm4py
from mako.util import to_list
from pm4py.objects.log.obj import EventLog, Trace, Event
from pm4py.statistics.attributes.log import get as attributes_get


"""
Currently implemented Polluters

Incomplete Data:
    Delete...   ...random activity              (DeleteActivityPolluter)
                ...random trace                 (DeleteTracePolluter)
    
Incorrect Data:
    Insert...   ...alien activity               (InsertAlienActivityPolluter)
                ...known activity               (InsertRandomActivityPolluter)
                ...duplicate activity           (InsertDuplicateActivityPolluter)
                ...duplicate trace              (InsertDuplicateTracePolluter)
    Replace...  ...alien activity               (ReplaceAlienActivityPolluter)
                ...known activity               (ReplaceRandomActivityPolluter)
                ...duplicate activity           (ReplaceDuplicateActivityPolluter)
                ...duplicate trace              (ReplaceDuplicateTracePolluter)
                
    Timestamp... ...delayed event logging       (DelayingEventLoggingPolluter)
    
Imprecise Data:
    Timestamp... ...aggregated event logging    (AggregatedEventLoggingPolluter)
    Replace...  ...precise event label          (PreciseActivityPolluter)
    Replace...  ...imprecise event label        (ImpreciseActivityPolluter)
    
Irrelevant Data:
    Insert...   ...alien activity               (InsertAlienActivityPolluter)
    Replace...  ...alien activity               (ReplaceAlienActivityPolluter)
"""


# TODO remove deepcopy calls. we do these in noisy_log_evaluation now!


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
    def __init__(self, percentage, alien_activity_nr=None):
        self.percentage = percentage
        self.alien_activity_nr = alien_activity_nr

    # I (Yannis) modified this polluter to take a number of alien activities instead of generating a different activity for each event (which really messed up the event log too much)
    # if you do not give in a number of alien activities, this number will be set to the number of events to insert and an activity label will be randomly drawn from this list (slightly different behaviour than original)
    def pollute(self, log):
        log_copy = copy.deepcopy(log)
        number_of_events = sum([len(tr) for tr in log])
        unique_activities = set()
        for tr in log:
            for e in tr:
                unique_activities.add(e['concept:name'])


        #TODO This mess of a fix will break so easily :(
        no_alien_activities = 0
        if self.alien_activity_nr is None:
            no_alien_activities = math.ceil(math.sqrt(len(unique_activities)))
        elif self.alien_activity_nr == "sqrt":
            no_alien_activities = math.ceil(math.sqrt(len(unique_activities)))
        elif 0.0 <= self.alien_activity_nr <= 1.0:
            no_alien_activities = math.ceil(self.alien_activity_nr * len(unique_activities))

        alien_activities = []

        to_duplicate = math.ceil(number_of_events * self.percentage)

        for _ in range(no_alien_activities):
            alien_activities.append(str(random.getrandbits(128)))

        for _ in range (to_duplicate):
            tr_idx = random.randint(0,len(log_copy)-1)
            tr = log_copy[tr_idx]

            to_insert = 0 if len(tr) <= 1 else random.randint(0, len(tr)-1)
            if len(tr) < to_insert:
                print(len(tr)-1,to_insert)
                print(tr)
            #if len(tr) <= 1:
            #    to_insert = 0
            #else:
            #    to_insert = random.randint(0, len(tr)-1)
            #new_event = {}
            #for x in tr[to_insert].keys():
            #    new_event[x]=tr[to_insert][x]

            new_event = copy.deepcopy(tr[to_insert])
            new_event['concept:name'] = random.choice(alien_activities)
            #new_event = Event(tr[to_insert])

            #new_event['concept:name'] = random.choice(alien_activities)
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
        #print(to_delete)
        for _ in range (to_delete):
            tr_idx = random.randint(0,len(log_copy)-1)
            tr = log_copy[tr_idx]
            #if trace has length 1 (i.e. 0 after removal of single activity), remove it from the log entirely
            if len(tr)==1:
                new_log = log_copy[:tr_idx] + log_copy[tr_idx + 1:]
                log_copy = EventLog(new_log)
                continue
            deletion_position = random.randint(0,len(tr))

            new_tr= tr[:deletion_position] + tr[deletion_position+1:]
            attributes = tr.attributes
            #print(len(log[tr_idx]),log[tr_idx])
            #print(tr.attributes)
            if len(attributes)==0:
                log_copy[tr_idx] = Trace(new_tr, **attributes)
            else:
                log_copy[tr_idx] = Trace(new_tr, **attributes)
            #log[tr_idx].attributes = attributes
            #print(len(log[tr_idx]), log[tr_idx])
            #print(log[tr_idx].attributes)

            #print(log_copy[tr_idx])
            #log_copy[tr_idx] = tr
            #print(log_copy[tr_idx])
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
    def __init__(self, percentage, alien_activity_nr= None):
        self.percentage = percentage
        self.alien_activity_nr = alien_activity_nr

    # I (Yannis) modified this polluter to take a number of alien activities instead of generating a different activity for each event (which really messed up the event log too much)
    # if you do not give in a number of alien activities, this number will be set to the number of events to insert and an activity label will be randomly drawn from this list (slightly different behaviour than original)
    def pollute(self, log):
        log_copy = copy.deepcopy(log)
        number_of_events = sum([len(tr) for tr in log])
        if self.alien_activity_nr is None:
            self.alien_activity_nr = math.sqrt(number_of_events)
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

    def __init__(self, percentage=1.0, distribution='gamma', parameters={'shape': 2, 'scale': 2}, mean_delay= None):
        self.percentage = percentage
        self.distribution = distribution
        self.parameters = parameters
        self.mean_delay = mean_delay

    def pollute(self, log):
        log_copy = deepcopy(log)
        number_of_events = sum([len(tr) for tr in log])

        if self.mean_delay is None:
            # compute a mean_delay depending on the average time between events in the log
            total_delta = timedelta(0)
            total_transitions = 0

            for trace in log:
                # Sort events in case they're not already ordered
                events = sorted(trace, key=lambda e: e['time:timestamp'])
                for i in range(1, len(events)):
                    delta = events[i]['time:timestamp'] - events[i - 1]['time:timestamp']
                    total_delta += delta
                    total_transitions += 1

            # Calculate average time between events
            self.mean_delay = total_delta.total_seconds() / 60 / total_transitions

        to_pollute = math.ceil(number_of_events * self.percentage)

        # compute a rescaling factor to get a delay with a mean = mean_delay based on a sampling of the gamma distribution
        rescale_factor = self.mean_delay / (self.parameters['shape'] * self.parameters['scale'])

        for _ in range(to_pollute):
            tr = log_copy[random.randint(0,len(log_copy)-1)]

            to_replace = 0 if len(tr) <= 1 else random.randint(0, len(tr)-1)

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
    def __init__(self, percentage=1.0, target_precision='hour'):
        self.percentage = percentage
        self.target_precision = target_precision

    # this function assumes that target_precision is more coarse than current precision
    def pollute(self, log):
        log_copy = copy.deepcopy(log)
        number_of_events = sum([len(tr) for tr in log])

        to_pollute = math.ceil(number_of_events * self.percentage)

        for _ in range(to_pollute):
            tr = log_copy[random.randint(0, len(log_copy) - 1)]
            to_replace = 0 if len(tr) <= 1 else random.randint(0, len(tr)-1)

            #print(tr[to_replace])
            #print(tr[to_replace]["time:timestamp"])
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
            attributes = tr.attributes

            log_copy[i] = Trace(new_tr, **attributes)

        return log_copy


class PreciseActivityPolluter(LogPolluter):
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

# polluter taking a list of precise activity labels and merging them into one (e.g., discharge in Sepsis)
class ImpreciseActivityPolluter(LogPolluter):
    """
    Replaces specified precise activity names of events with a more coarse-grained one

    Example: A_1, A_2 -> A, A
    """
    def __init__(self, precise_activity_labels, new_activity_label):
        self.precise_activity_labels = precise_activity_labels
        self.new_activity_label = new_activity_label
        self.percentage = None


    def pollute(self, log):
        log_copy = deepcopy(log)

        # loop through the events in the log
        for i, tr in enumerate(log_copy):
            #print(tr)
            for j, event in enumerate(tr):
                # replace precise_activity_labels with new_activity_label
                if tr[j]["concept:name"] in self.precise_activity_labels:
                    tr[j]["concept:name"] = self.new_activity_label

        return log_copy


def create_pollution_testbed():
    percentages = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]

    insert_random_activity_polluters = [InsertRandomActivityPolluter(x) for x in percentages]
    insert_duplicate_activity_polluters = [InsertDuplicateActivityPolluter(x) for x in percentages]
    insert_alien_activity_polluters_sqrt = [InsertAlienActivityPolluter(x,"sqrt") for x in percentages]
    insert_alien_activity_polluters_fixed = [InsertAlienActivityPolluter(x,0.2) for x in percentages]


    replace_random_activity_polluters = [ReplaceRandomActivityPolluter(x) for x in percentages]
    replace_duplicate_activity_polluters = [ReplaceDuplicateActivityPolluter(x) for x in percentages]
    replace_alien_activity_polluters = [ReplaceAlienActivityPolluter(x) for x in percentages]

    delete_random_activity_polluters = [DeleteActivityPolluter(x) for x in percentages]

    insert_duplicate_trace_polluters = [InsertDuplicateTracePolluter(x) for x in percentages]
    delete_random_trace_polluters = [DeleteTracePolluter(x) for x in percentages]

    imprecise_activity_polluters = [ImpreciseActivityPolluter(precise_activity_labels=['Release A', 'Release B', 'Release C', 'Release D', 'Release E'], new_activity_label='Release')]
    delay_event_logging_polluters = [DelayedEventLoggingPolluter(x, mean_delay=120) for x in percentages]
    aggregate_timestamp_polluters_hourly = [AggregatedEventLoggingPolluter(percentage=x, target_precision='hour') for x in percentages]
    aggregate_timestamp_polluters_daily = [AggregatedEventLoggingPolluter(percentage=x, target_precision='day') for x in percentages]

    precise_activity_polluters = [PreciseActivityPolluter(percentage=x) for x in percentages]

    return (insert_alien_activity_polluters_sqrt +
            aggregate_timestamp_polluters_hourly +
            aggregate_timestamp_polluters_daily +
            delay_event_logging_polluters +
            delete_random_activity_polluters +
            imprecise_activity_polluters)
            #insert_alien_activity_polluters_fixed)

#    return (insert_random_activity_polluters +
#                 insert_duplicate_activity_polluters +
#                 insert_alien_activity_polluters +
#                 replace_random_activity_polluters +
#                 replace_duplicate_activity_polluters +
#                 replace_alien_activity_polluters +
#                 delete_random_activity_polluters +
#                 insert_duplicate_trace_polluters +
#                 delete_random_trace_polluters +
#                 delay_event_logging_polluters +
#                 aggregate_timestamp_polluters
#            )


#delete_random_activity_polluters = [DeleteActivityPolluter(x) for x in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]]
#log = pm4py.read_xes(os.path.join("in", "logs", "RTFM_perfect_fitting_cases.xes"), return_legacy_log_object=True)
#net, im, fm = pm4py.read_pnml(os.path.join("in", "models", "Sepsis_inductive.pnml"))

#for p in delete_random_activity_polluters:
#    p2 = p.pollute(log)
#    m, im, fm = pm4py.discovery.discover_petri_net_inductive(p2, noise_threshold=0.2)

#    polluted_fitness_tbr = pm4py.conformance.fitness_token_based_replay(p2, m, im, fm)
#    polluted_precision_tbr = pm4py.conformance.precision_token_based_replay(p2, m, im, fm)
#    polluted_generalization_tbr = pm4py.conformance.generalization_tbr(p2, m, im, fm)

#    print(polluted_fitness_tbr['average_trace_fitness'], polluted_precision_tbr, polluted_generalization_tbr)