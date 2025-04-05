import random
import math

# --------------------
# GLOBAL PARAMETERS
# --------------------
LAMBDA = 1.0          # Arrival rate
MU_T = 0.476190476    # Triage nurse service rate
MU_S = 0.16           # Stable home-care rate
MU_CB = 0.118518519   # Hospital bed service rate
P_STABLE = 0.2        # Probability stable
P_CRITICAL = 0.8      # Probability critical

S = 3   # Number of triage nurses
K = 9   # Number of hospital beds

# Group-specific random seed
SEED = 4040800189
random.seed(SEED)

def GenerateInterarrival():
    return random.expovariate(LAMBDA)


def GenerateNurseServiceTime():
    return random.expovariate(MU_T)

def GenerateHospitalHealingTime():
    return random.expovariate(MU_CB)

def GenerateHomeHealingTime(condition='s'):
    """
    condition='s' => stable, home-care ~ Exp(MU_S).
    condition='c' => forced-home critical => ~ Exp(MU_CB / alpha).
    """
    if condition == 's':
        return random.expovariate(MU_S)
    else:
        alpha = random.uniform(1.25, 1.75)
        return random.expovariate(MU_CB / alpha)
    
# We'll keep a global dictionary for the state
# so our event functions can access/update it.

state = {
    'clock': 0.0,
    'numberInTriageQueue': 0,
    'busyNurses': 0,
    'occupiedBeds': 0,
    'patientsHealed': 0,     # count how many have completed
    # For output collection:
    'totalArrivals': 0,
    'rejectedCritical': 0,
}

# We'll store the FEL as a list of events:
FEL = []

# For storing event history (to produce the table of first 20 events)
event_history = []

def schedule_event(time, etype, patientID=None, extra=None):
    FEL.append((time, etype, patientID, extra))

def get_next_event():
    # Sort by time and pop earliest
    FEL.sort(key=lambda x: x[0])
    return FEL.pop(0)

def Arrival(event):
    global state, FEL

    # Update clock
    state['clock'] = event[0]

    # Record arrival
    state['totalArrivals'] += 1

    # Schedule next arrival
    next_arrival_time = state['clock'] + GenerateInterarrival()
    schedule_event(next_arrival_time, 'Arrival')

    # Check triage
    if state['busyNurses'] < S:
        # Start triage immediately
        state['busyNurses'] += 1
        departure_time = state['clock'] + GenerateNurseServiceTime()
        schedule_event(departure_time, 'DepartureTriage')
    else:
        # queue
        state['numberInTriageQueue'] += 1


def DepartureTriage(event):
    global state, FEL

    # Update clock
    state['clock'] = event[0]

    # If queue > 0, immediately start next triage
    if state['numberInTriageQueue'] > 0:
        state['numberInTriageQueue'] -= 1
        departure_time = state['clock'] + GenerateNurseServiceTime()
        schedule_event(departure_time, 'DepartureTriage')
    else:
        state['busyNurses'] -= 1

    # Decide stable vs. critical
    if random.random() < P_STABLE:
        # stable => home
        home_time = state['clock'] + GenerateHomeHealingTime('s')
        schedule_event(home_time, 'RecoveryHome', extra={'isStable': True})
    else:
        # critical => need bed
        if state['occupiedBeds'] < K:
            state['occupiedBeds'] += 1
            discharge_time = state['clock'] + GenerateHospitalHealingTime()
            schedule_event(discharge_time, 'TreatedAtHospital')
        else:
            # forced home
            state['rejectedCritical'] += 1
            home_time = state['clock'] + GenerateHomeHealingTime('c')
            schedule_event(home_time, 'RecoveryHome', extra={'isStable': False})


def TreatedAtHospital(event):
    global state, FEL
    # Update clock
    state['clock'] = event[0]
    # free a bed
    state['occupiedBeds'] -= 1
    # patient is healed
    state['patientsHealed'] += 1

def RecoveryHome(event):
    global state, FEL
    # Update clock
    state['clock'] = event[0]
    # patient done
    state['patientsHealed'] += 1
def run_simulation(target_healed, max_events, initial_condition='empty'):
    """
    Runs an event-based simulation until 'target_healed' patients have completed.
    Returns a list of event snapshots (for the first 20 events) and final stats.
    """
    # Reset the global state
    global state, FEL, event_history

    state = {
        'clock': 0.0,
        'numberInTriageQueue': 0,
        'busyNurses': 0,
        'occupiedBeds': 0,
        'patientsHealed': 0,
        'totalArrivals': 0,
        'rejectedCritical': 0,
    }
    FEL = []
    event_history = []

    # --- Initialize FEL with first arrival:
    first_arrival = GenerateInterarrival()
    schedule_event(first_arrival, 'Arrival')

    # --- Apply initial condition if needed:
    if initial_condition == 'half':
        # fill about half nurses & half beds:
        state['busyNurses'] = math.floor(S/2)
        state['occupiedBeds'] = math.floor(K/2)
    elif initial_condition == 'full':
        # fill all nurses & beds:
        state['busyNurses'] = S
        state['occupiedBeds'] = K
    # (You might also schedule partial triage/hospital departure events if you want them to finish eventually, 
    # but that is optional, depending on how you interpret “starting full.” 
    # The assignment might only want the resources "occupied" from time zero.)

    num_events = 0

    # --- Main loop
    while state['patientsHealed'] < target_healed and num_events < max_events and len(FEL) > 0:
        # get next event
        e = get_next_event()
        num_events += 1

        # Execute event
        etype = e[1]
        if etype == 'Arrival':
            Arrival(e)
        elif etype == 'DepartureTriage':
            DepartureTriage(e)
        elif etype == 'TreatedAtHospital':
            TreatedAtHospital(e)
        elif etype == 'RecoveryHome':
            RecoveryHome(e)
        else:
            pass  # unknown event type

        # Record the event in event_history (especially the first 20)
        if num_events <= 20:
            event_history.append({
                'Event#': num_events,
                'Clock': round(state['clock'], 4),
                'EventType': etype,
                'TriageQueue': state['numberInTriageQueue'],
                'BusyNurses': state['busyNurses'],
                'OccupiedBeds': state['occupiedBeds'],
                'PatientsHealed': state['patientsHealed']
            })

    # After loop, collect final stats
    total_healed = state['patientsHealed']
    total_arrived = state['totalArrivals']
    reject_crit = state['rejectedCritical']

    # You can compute additional metrics. For instance:
    # - proportion of critical patients that are rejected
    # - etc.

    # Create a dictionary with final results
    results = {
        'healed': total_healed,
        'arrived': total_arrived,
        'rejected_critical': reject_crit,
        'rejection_rate': reject_crit / total_arrived if total_arrived > 0 else 0.0,
        # You can add more stats (utilization, etc.) if you track them in your code
    }

    # Return the first-20-event table plus final results
    return event_history, results

# Example usage:
ev_history, final_stats = run_simulation(target_healed=20, max_events=999999999,initial_condition='empty')

print("Table of first 20 events (or fewer if simulation ends earlier):")
for row in ev_history:
    print(row)

print("\nFinal Stats:", final_stats)