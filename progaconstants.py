
import math


LISTEN_PORT = 8080

PLAYER_SLEEP_SECONDS = 0.5
FS_RECORDED_TRACK_PERIOD = 0.25
FASTER = 200
PLAYER_POINTER_INCREMENT = int(PLAYER_SLEEP_SECONDS / FS_RECORDED_TRACK_PERIOD)*FASTER

PREDICTION_SLEEP_SECONDS = 2

WUPDATE_SECONDS = 3


MYSTATE_CHANNEL_NAME = 'my-state-updated'
UPDATED_TRAFFIC_CHANNEL_NAME = 'traffic-updated'
INITIAL_WEIGHTS_COMPUTED_CHANNEL_NAME = 'initial-weights-computed'
SIMULATION_FINISHED_CHANNEL_NAME = 'simulation-finished'
SIMULATION_STOPPED_CHANNEL_NAME = 'simulation-stopped'
SIMULATION_STARTED_CHANNEL_NAME = 'simulation-started'

ITEM_MY_STATE = 'myState'
ITEM_TRAFFIC = 'traffic'

SCENARIO_INFO_FILENAME = 'scenario_info.json'
SCENARIOS_FOLDER = "./scenarios"

#######
LAT0 = 48.80971511758816
LAT0R = math.radians(LAT0)
#LAT0R = 0.8518902357623647
LON0 = 2.0701075993077054
#LON0R = 0.036130193478474945
LON0R = math.radians(LON0)
EARTHRADIUS = 6371000.0 # in meters

DECLARED_INTENT_PROBABILITY = 0.95

BETA_POS = 0.1
BETA_TRK = 0.1

