""" Reprensentations of some elements that can be found in an Android app. """


class ManifestElement(object):
    """ Abstract manifest element used as base for other element types. """

    def __init__(self, name):
        self.name = name

    @property
    def short_name(self):
        """ Last part of the element name (stripping off a package name). """
        return self.name.split(".")[-1]


class Activity(ManifestElement):
    """ Activity of an Android application. """

    def __init__(self, name):
        super(Activity, self).__init__(name)
        self.intents = []

    def is_main_activity(self):
        has_action_main = False
        has_category_launcher = False
        for intent in self.intents:
            if ( intent.type == Intent.TYPE.ACTION
                 and intent.name == "android.intent.action.MAIN" ):
                has_action_main = True
            if ( intent.type == Intent.TYPE.CATEGORY
                 and intent.name == "android.intent.category.LAUNCHER" ):
                has_category_launcher = True

        return has_action_main and has_category_launcher


class Service(ManifestElement):
    """ Service registered for an Android application. """
    pass

class Provider(ManifestElement):
    """ Service registered for an Android application. """
    pass

class Receiver(ManifestElement):
    """ Receiver of some Intents in an Android application. """

    def __init__(self, name):
        super(Receiver, self).__init__(name)
        self.intents = []


class Intent(ManifestElement):
    """ Intent used in an Android application. """

    class TYPE(object):
        """ Intent type """

        UNKNOWN = -1
        ACTION = 0
        CATEGORY = 1

        @staticmethod
        def tag_value(v):
            if v == "action":
                return Intent.TYPE.ACTION
            elif v == "category":
                return Intent.TYPE.CATEGORY
            else:
                return Intent.TYPE.UNKNOWN

    def __init__(self, name, intent_type):
        super(Intent, self).__init__(name)
        self.type = intent_type


class Permission(ManifestElement):
    """ Permission given to an Android application. """
    pass
