# March 29 2018
# Google Analytics launch tracking logic.
# Generalized and pulled into its own module to simplify use in other apps.

import os, pickle, uuid

import UniversalAnalytics

class Tracker():
    # uuid_path - path to pickle file containing UUID
    # ga_id_components - list of the components of a GA ID to be combined with '-'
    # to avoid hard-coded ID string in code, every so slightly obfuscating it
    # to foil only the very dumbest trackers skimming GitHub for GA IDs.
    # user_defined_id - if not None, overrides auto-generated UUID with specified string
    def __init__(self, uuid_path, ga_id_components, user_defined_uuid=None):
        self.uuid_path = uuid_path
        self.ga_id = '-'.join(ga_id_components)
        self.user_defined_uuid = user_defined_uuid

    # ping launch tracker, creating and saving UUID if it none exists
    def ping(self):
        user_uuid = self.get_uuid()
        tracker = UniversalAnalytics.Tracker.create(self.ga_id, client_id=user_uuid)
        tracker.send('pageview', path='/', title='launch: UUID={}'.format(user_uuid))        

    # retrieve existing UUID from uuid_path or create new UUID if none exists
    def get_uuid(self):
        user_uuid = None
        if os.path.exists(self.uuid_path):
            with open(self.uuid_path, 'r') as uuidFileStream:
                user_uuid = pickle.load(uuidFileStream)
        else:
            user_uuid = self.create_uuid()
            print("new UUID = {}".format(user_uuid))
            self.write_uuid(user_uuid)
        return user_uuid

    # create UUID, or use user_defined_uuid if defined
    def create_uuid(self):
        return self.user_defined_uuid if self.user_defined_uuid else uuid.uuid4()

    # write UUID to file
    def write_uuid(self, out_uuid):
        with open(self.uuid_path, 'wb') as uuidFileStream:
            pickle.dump(out_uuid, uuidFileStream)

    # change UUID without pinging - intended for use by devs to create an ID
    # easily distinguishable from the auto-generated UUIDs of actual users
    def update_uuid(self, new_uuid):
        self.write_uuid(new_uuid)
