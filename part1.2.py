import random

# For demonstration, let's define some global parameters here.
# In practice, you might structure them differently or store them in a config class.
LAMBDA = 1.0               # arrival rate (patients/hour)
MU_T = 0.476190476         # triage nurse service rate
MU_S = 0.16                # stable home-care rate
MU_CB = 0.118518519        # hospital bed service rate
P_STABLE = 0.2             # Probability that a patient is stable
P_CRITICAL = 1 - P_STABLE  # Probability that a patient is critical

S = 3  # number of triage nurses
K = 9  # number of hospital beds

# For random number seeding, use your group's seed:
MY_SEED = 4040800189  # or sum of your group members' IDs
random.seed(MY_SEED)

def GenerateInterarrival():
    """
    Returns an exponentially distributed interarrival time
    with rate LAMBDA.
    """
    return random.expovariate(LAMBDA)

def GenerateNurseServiceTime():
    """
    Returns an exponentially distributed service time
    for triage nurses with rate MU_T.
    """
    return random.expovariate(MU_T)

def GenerateHospitalHealingTime():
    """
    Returns an exponentially distributed healing time
    for critical patients in a hospital bed (rate = MU_CB).
    """
    return random.expovariate(MU_CB)

def GenerateHomeHealingTime(condition='s'):
    """
    Returns an exponentially distributed healing time for a patient who is home.
      - If 's': stable patient at home, rate = MU_S.
      - If 'c': critical patient forced to go home. We first sample alpha ~ Uniform[1.25, 1.75].
        Then the rate = MU_CB / alpha, making the mean 1/(MU_CB/alpha) = alpha / MU_CB.
    """
    if condition == 's':
        # Stable patient at home
        return random.expovariate(MU_S)
    else:
        # Critical patient forced to go home
        alpha = random.uniform(1.25, 1.75)
        # The rate is scaled by alpha
        return random.expovariate(MU_CB / alpha)
    
    # Example event structure: (eventTime, eventType, patientID, extraInfo)
#   eventTime : the simulation time at which event occurs
#   eventType : e.g. 'Arrival', 'DepartureTriage', 'TreatedAtHospital', 'RecoveryHome'
#   patientID : an identifier for the patient (optional, but useful)
#   extraInfo : any other data you need (e.g. stable/critical, etc.)

# We'll keep a global list (or priority queue) for the FEL:
FEL = []

# State variables:
currentTime = 0.0
numberInTriageQueue = 0
busyNurses = 0
occupiedBeds = 0

# Additional counters/statistics, such as:
totalPatientsArrived = 0
totalPatientsHealed = 0
rejectedCriticalCount = 0

# And so forth...

def Arrival(event):
    """
    Handle the arrival of a new patient.
    event is assumed to be (time, 'Arrival', patientID, {})
    """
    global currentTime, numberInTriageQueue, busyNurses, totalPatientsArrived

    # 1) Update simulation clock to this event's time
    currentTime = event[0]

    # 2) Increment counters
    totalPatientsArrived += 1

    # 3) Schedule the next arrival
    interarrival_time = GenerateInterarrival()
    next_arrival_time = currentTime + interarrival_time
    FEL.append((next_arrival_time, 'Arrival', None, {}))

    # 4) Check if a triage nurse is free
    if busyNurses < S:
        # Nurse is available immediately
        busyNurses += 1
        service_time = GenerateNurseServiceTime()
        departure_triage_time = currentTime + service_time

        # We'll store patient info in extraInfo if needed
        FEL.append((departure_triage_time, 'DepartureTriage', None, {}))
    else:
        # No free nurse, patient must join the queue
        numberInTriageQueue += 1

def DepartureTriage(event):
    """
    Handle a patient's completion of triage service.
    event is assumed to be (time, 'DepartureTriage', patientID, extraInfo)
    """
    global currentTime, numberInTriageQueue, busyNurses, occupiedBeds, rejectedCriticalCount

    # 1) Update clock
    currentTime = event[0]

    # 2) If there is a queue waiting, immediately take next patient for triage
    if numberInTriageQueue > 0:
        numberInTriageQueue -= 1
        # Start service for next patient
        service_time = GenerateNurseServiceTime()
        departure_time = currentTime + service_time
        FEL.append((departure_time, 'DepartureTriage', None, {}))
    else:
        # Nurse becomes idle
        busyNurses -= 1

    # 3) Determine if this departing patient is stable or critical
    if random.random() < P_STABLE:
        # Stable -> schedule home recovery event
        home_time = GenerateHomeHealingTime(condition='s')
        FEL.append((currentTime + home_time, 'RecoveryHome', None, {'isStable': True}))
    else:
        # Critical
        if occupiedBeds < K:
            # Admit to hospital bed
            occupiedBeds += 1
            hospital_healing_time = GenerateHospitalHealingTime()
            FEL.append((currentTime + hospital_healing_time, 'TreatedAtHospital', None, {}))
        else:
            # Forced home (bed not available)
            rejectedCriticalCount += 1
            home_time = GenerateHomeHealingTime(condition='c')
            FEL.append((currentTime + home_time, 'RecoveryHome', None, {'isStable': False}))

def TreatedAtHospital(event):
    """
    Handle a critical patient's discharge from the hospital.
    event is (time, 'TreatedAtHospital', patientID, extraInfo)
    """
    global currentTime, occupiedBeds

    # 1) Update clock
    currentTime = event[0]

    # 2) One bed becomes free
    occupiedBeds -= 1

    # 3) Patient leaves system - if you want to record stats about total heal times,
    #    you'd do it here (e.g., event[0] - patient.arrival_time, etc.)
    #    but for now, just note that the patient is done.

    # No further events for this patient.
    pass
def RecoveryHome(event):
    """
    Handle a patient's completion of home-care.
    event is (time, 'RecoveryHome', patientID, extraInfo)
    """
    global currentTime

    # 1) Update clock
    currentTime = event[0]

    # 2) This patient leaves the system. We can record stats if needed, e.g. total time in system.
    #    If extraInfo['isStable'] is True, we know it's a stable patient, else a forced-home critical.

    pass
def get_next_event():
    """
    Pop the soonest event from the FEL.
    """
    # Make sure your FEL is sorted by time
    FEL.sort(key=lambda e: e[0])
    return FEL.pop(0)  # remove and return the first event

def main_simulation_loop(max_events=50):
    """
    A simple loop that processes events until max_events are executed,
    or you can stop by another condition (e.g., number of recovered patients).
    """
    event_count = 0
    while event_count < max_events and len(FEL) > 0:
        next_event = get_next_event()
        event_type = next_event[1]

        if event_type == 'Arrival':
            Arrival(next_event)
        elif event_type == 'DepartureTriage':
            DepartureTriage(next_event)
        elif event_type == 'TreatedAtHospital':
            TreatedAtHospital(next_event)
        elif event_type == 'RecoveryHome':
            RecoveryHome(next_event)
        else:
            # Unrecognized event
            pass

        event_count += 1