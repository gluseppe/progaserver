
import math


LISTEN_PORT = 8080

PLAYER_SLEEP_SECONDS = 0.25
FS_RECORDED_TRACK_PERIOD = 0.25
FASTER = 1
PLAYER_POINTER_INCREMENT = int(PLAYER_SLEEP_SECONDS / FS_RECORDED_TRACK_PERIOD)*FASTER

PREDICTION_SLEEP_SECONDS = 2

WUPDATE_SECONDS = 3


MYSTATE_CHANNEL_NAME = 'my-state-updated'
UPDATED_TRAFFIC_CHANNEL_NAME = 'traffic-updated'
INITIAL_WEIGHTS_COMPUTED_CHANNEL_NAME = 'initial-weights-computed'
SIMULATION_FINISHED_CHANNEL_NAME = 'simulation-finished'
SIMULATION_STOPPED_CHANNEL_NAME = 'simulation-stopped'
SIMULATION_STARTED_CHANNEL_NAME = 'simulation-started'
PROGA_IS_READY_CHANNEL_NAME = 'proga-ready'
SCENARIO_LOADED_CHANNEL_NAME = 'scenario-loaded'


COORDS_TYPE_GEO = 'geo'
COORDS_TYPE_PLANE = 'plane'

ITEM_MY_STATE = 'myState'
ITEM_TRAFFIC = 'traffic'

SCENARIO_INFO_FILENAME = 'scenario_info.json'
SCENARIOS_FOLDER = "./scenarios"
SELF_FLIGHT_ID = "SELF000"

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

NUMPARTICLES = 100
GRIDBINS_X = 3
GRIDBINS_Y = 4
GRIDBINS_Z = 2
GRIDBINS = (GRIDBINS_X, GRIDBINS_Y, GRIDBINS_Z)

ECC = 0.75
LOCRADIUS = 500. # meters
PENAL_GLOBAL = 0.1**8
PENAL_ANGLE = 0.1**3
PENAL_DIST = 0.1**3
PI = 3.141592653589793
ANGLE_GAP = PI/12 # 15. degrees
BETA_DIST = 0.1**3 # meters^{-1}
BETA_ANGLE = 5 


