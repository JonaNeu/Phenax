import json


def generate_target_list(json_filepath):
    with open(json_filepath, "r") as json_file:
        targets_data = json.load(json_file)

    targets = []
    for target_data in targets_data:
        targets.append(generate_target(target_data))
    return targets


def generate_target(target_data):
    alerts = []
    for alert_data in target_data["alerts"]:
        alerts.append(generate_alert(alert_data))
    return Target(target_data["method"], alerts, target_data["score"])


def generate_alert(alert_data):
    return Alert(alert_data["category"], alert_data["score"],
                 alert_data["instruction"], alert_data["key"])


class Target(object):

    def __init__(self, method_name, alerts, score):
        self.method_name = method_name
        self.alerts = alerts
        self.score = score

    def __str__(self):
        return "RS {rs} ({num_alerts} of type {types}) in {method}".format(
            method = self.method_name,
            rs = self.score,
            num_alerts = len(self.alerts),
            types = ", ".join(set([alert.category for alert in self.alerts]))
        )

    def get_types(self):
        types = {}
        for alert in self.alerts:
            if alert.category not in types:
                types[alert.category] = 1
            else:
                types[alert.category] += 1
        return types


class Alert(object):

    def __init__(self, category, score, instruction, key):
        self.category = category
        self.score = score
        self.instruction = instruction
        self.key = key

    def __str__(self):
        return ("Alert at " + str(self.key) + " " +
                "(type: " + self.category +
                ", RS: " + str(self.score) + ")")
