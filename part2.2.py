import random
import math

# ===============================
# GLOBAL PARAMETERS
# ===============================
LAMBDA = 1.0          # Arrival rate
MU_T = 0.476190476    # Triage nurse service rate
MU_S = 0.16           # Stable home-care rate
MU_CB = 0.118518519   # Hospital bed service rate
P_STABLE = 0.2        # Probability stable
P_CRITICAL = 0.8      # Probability critical

S = 3   # Number of triage nurses
K = 9   # Number of hospital beds

SEED = 4040800189


# ===============================
# RANDOM VARIATE GENERATORS
# ===============================
def GenerateInterarrival():
    return random.expovariate(LAMBDA)

def GenerateNurseServiceTime():
    return random.expovariate(MU_T)

def GenerateHospitalHealingTime():
    return random.expovariate(MU_CB)

def GenerateHomeHealingTime(condition='s'):
    """ 
    condition='s' => stable (Exp(MU_S))
    condition='c' => forced-home critical => Exp(MU_CB/alpha)
    """
    if condition == 's':
        return random.expovariate(MU_S)
    else:
        alpha = random.uniform(1.25, 1.75)
        return random.expovariate(MU_CB / alpha)


# ===============================
# GLOBAL STATE & STRUCTURES
# ===============================
state = {}
FEL = []
event_history = []

# Tracking each patient's arrival_time, etc.
patient_info = {}
next_patient_id = 0


# ===============================
# SCHEDULE / GET EVENTS
# ===============================
def schedule_event(time, etype, patientID=None, extra=None):
    FEL.append((time, etype, patientID, extra))

def get_next_event():
    FEL.sort(key=lambda x: x[0])
    return FEL.pop(0)

# ===============================
# EVENT FUNCTIONS
# ===============================
def Arrival(event):
    """A new patient arrives to triage (or queue)."""
    global state, FEL, next_patient_id, patient_info

    state['clock'] = event[0]

    pid = next_patient_id
    next_patient_id += 1
    # Record arrival time
    patient_info[pid] = {'arrival_time': state['clock']}

    state['totalArrivals'] += 1

    # Schedule next arrival
    next_arr_time = state['clock'] + GenerateInterarrival()
    schedule_event(next_arr_time, 'Arrival')

    # Check if nurse free
    if state['busyNurses'] < S:
        state['busyNurses'] += 1
        finish_time = state['clock'] + GenerateNurseServiceTime()
        schedule_event(finish_time, 'DepartureTriage', pid)
    else:
        state['numberInTriageQueue'] += 1


def DepartureTriage(event):
    """A patient finishes triage and is either stable or critical."""
    global state, FEL, patient_info

    current_time = event[0]
    state['clock'] = current_time
    pid = event[2]  # who finished triage

    # If triage queue > 0, immediately start next triage
    if state['numberInTriageQueue'] > 0:
        state['numberInTriageQueue'] -= 1
        # We'll create a new patient ID or re-use logic (in reality you store the queue).
        # For simplicity, let's create a new ID with partial data.
        global next_patient_id
        new_pid = next_patient_id
        
        next_patient_id += 1
        patient_info[new_pid] = {'arrival_time': current_time}  # minimal

        finish2 = current_time + GenerateNurseServiceTime()
        schedule_event(finish2, 'DepartureTriage', new_pid)
    else:
        # Freed a nurse
        state['busyNurses'] -= 1

    # Classify stable vs. critical
    if random.random() < P_STABLE:
        # stable
        state['stableCount'] += 1
        done_home = current_time + GenerateHomeHealingTime('s')
        schedule_event(done_home, 'RecoveryHome', pid, {'isStable': True})
    else:
        # critical
        state['criticalCount'] += 1
        if state['occupiedBeds'] < K:
            state['occupiedBeds'] += 1
            done_bed = current_time + GenerateHospitalHealingTime()
            schedule_event(done_bed, 'TreatedAtHospital', pid)
        else:
            # forced home
            state['rejectedCritical'] += 1
            done_home = current_time + GenerateHomeHealingTime('c')
            schedule_event(done_home, 'RecoveryHome', pid, {'isStable': False})


def TreatedAtHospital(event):
    """A critical patient finishes hospital care."""
    global state, FEL, patient_info
    current_time = event[0]
    state['clock'] = current_time
    pid = event[2]

    state['occupiedBeds'] -= 1
    state['patientsHealed'] += 1

    # record time in system
    arr_time = patient_info[pid]['arrival_time'] if pid in patient_info else 0.0
    state['sum_time_in_system'] += (current_time - arr_time)
    state['count_patients_finished'] += 1


def RecoveryHome(event):
    """A stable or forced-home critical finishes home care."""
    global state, FEL, patient_info
    current_time = event[0]
    state['clock'] = current_time
    pid = event[2]

    state['patientsHealed'] += 1

    # record time in system
    arr_time = patient_info[pid]['arrival_time'] if pid in patient_info else 0.0
    state['sum_time_in_system'] += (current_time - arr_time)
    state['count_patients_finished'] += 1

# ===============================
# APPLY INITIAL CONDITIONS
# (Schedules "already-busy" resources)
# ===============================
def apply_initial_condition(initial_condition):
    """
    If 'half': schedule half triage nurses & half beds as busy from time 0,
               each with a random finishing time.
    If 'full': schedule all triage nurses & all beds as busy from time 0.
    This ensures they eventually free up, 
    instead of staying occupied forever.
    """
    global state, FEL, next_patient_id, patient_info

    if initial_condition == 'half':
        # half nurses
        half_nurses = math.floor(S/2)
        for i in range(half_nurses):
            pid = next_patient_id
            next_patient_id += 1
            # patient arrived at time 0
            patient_info[pid] = {'arrival_time': 0.0}

            finish_t = random.expovariate(MU_T)
            schedule_event(finish_t, 'DepartureTriage', pid)
        state['busyNurses'] = half_nurses

        # half beds
        half_beds = math.floor(K/2)
        for i in range(half_beds):
            pid = next_patient_id
            next_patient_id += 1
            patient_info[pid] = {'arrival_time': 0.0}  # started hospital at time 0

            finish_b = random.expovariate(MU_CB)
            schedule_event(finish_b, 'TreatedAtHospital', pid)
        state['occupiedBeds'] = half_beds

    elif initial_condition == 'full':
        # all nurses
        for i in range(S):
            pid = next_patient_id
            next_patient_id += 1
            patient_info[pid] = {'arrival_time': 0.0}

            finish_t = random.expovariate(MU_T)
            schedule_event(finish_t, 'DepartureTriage', pid)
        state['busyNurses'] = S

        # all beds
        for i in range(K):
            pid = next_patient_id
            next_patient_id += 1
            patient_info[pid] = {'arrival_time': 0.0}

            finish_b = random.expovariate(MU_CB)
            schedule_event(finish_b, 'TreatedAtHospital', pid)
        state['occupiedBeds'] = K
    else:
        # 'empty' do nothing
        pass


# ===============================
# MAIN SIMULATION
# ===============================
def run_simulation(target_healed, max_events, initial_condition):
    """
    Runs the simulation until 'target_healed' patients have completed.
    Returns (event_history, results_dict).
    """
    global state, FEL, event_history, patient_info, next_patient_id

    # Reset everything
    random.seed(SEED)  # or remove if you want different seeds per run
    state = {
        'clock': 0.0,
        'numberInTriageQueue': 0,
        'busyNurses': 0,
        'occupiedBeds': 0,
        'patientsHealed': 0,
        'totalArrivals': 0,
        'rejectedCritical': 0,
        'stableCount': 0,
        'criticalCount': 0,
        'sum_time_in_system': 0.0,
        'count_patients_finished': 0,
    }
    FEL = []
    event_history = []
    patient_info = {}
    next_patient_id = 0

    # Time-based accumulators
    last_event_time = 0.0
    total_time_triage_empty = 0.0
    total_time_beds_empty = 0.0
    total_time_both_empty = 0.0
    nurse_busy_time = 0.0
    beds_occupied_time = 0.0

    # 1) Schedule the first arrival
    first_arrival = GenerateInterarrival()
    schedule_event(first_arrival, 'Arrival')

    # 2) Apply initial condition:
    apply_initial_condition(initial_condition)

    # 3) Main loop
    num_events = 0
    while state['patientsHealed'] < target_healed and num_events < max_events and len(FEL) > 0:
        e = get_next_event()
        current_time = e[0]
        event_type = e[1]

        delta = current_time - last_event_time

        # Accumulate time-based stats
        # triage empty => busyNurses==0 and queue==0
        if state['busyNurses']==0 and state['numberInTriageQueue']==0:
            total_time_triage_empty += delta
        # beds empty => occupiedBeds==0
        if state['occupiedBeds']==0:
            total_time_beds_empty += delta
        # both empty
        if (state['busyNurses']==0 and state['numberInTriageQueue']==0 
            and state['occupiedBeds']==0):
            total_time_both_empty += delta

        # usage
        nurse_busy_time += (state['busyNurses'] * delta)
        beds_occupied_time += (state['occupiedBeds'] * delta)

        # Update clock
        last_event_time = current_time

        # Process
        if event_type == 'Arrival':
            Arrival(e)
        elif event_type == 'DepartureTriage':
            DepartureTriage(e)
        elif event_type == 'TreatedAtHospital':
            TreatedAtHospital(e)
        elif event_type == 'RecoveryHome':
            RecoveryHome(e)
        else:
            pass

        num_events += 1

        # Record first 20 events
        if num_events <= 20:
            event_history.append({
                'Event#': num_events,
                'Clock': round(state['clock'], 4),
                'EventType': event_type,
                'TriageQueue': state['numberInTriageQueue'],
                'BusyNurses': state['busyNurses'],
                'OccupiedBeds': state['occupiedBeds'],
                'PatientsHealed': state['patientsHealed']
            })

    # End loop
    sim_time = state['clock']

    # Now compute final measures

    # 1) Prob triage empty
    prob_triage_empty = total_time_triage_empty/sim_time if sim_time>0 else 0.0
    # 2) Prob beds empty
    prob_beds_empty = total_time_beds_empty/sim_time if sim_time>0 else 0.0
    # 3) Prob both empty
    prob_both_empty = total_time_both_empty/sim_time if sim_time>0 else 0.0

    # 4) Average nurse util
    avg_nurse_util = (nurse_busy_time/(sim_time * S)) if sim_time>0 else 0.0
    # 5) Average #occupied beds
    avg_occupied_beds = (beds_occupied_time/sim_time) if sim_time>0 else 0.0

    # 6) Proportion critical rejected
    if state['criticalCount']>0:
        crit_reject_rate = state['rejectedCritical']/state['criticalCount']
    else:
        crit_reject_rate = 0.0

    # 7) Proportion treated at home
    forced_home = state['rejectedCritical']
    stable_home = state['stableCount']
    total_home = forced_home + stable_home
    if state['totalArrivals']>0:
        prop_home = total_home / state['totalArrivals']
    else:
        prop_home = 0.0

    # 8) Average time in system
    if state['count_patients_finished']>0:
        avg_time_sys = state['sum_time_in_system']/state['count_patients_finished']
    else:
        avg_time_sys = 0.0

    results = {
        'final_clock': sim_time,
        'healed': state['patientsHealed'],
        'arrived': state['totalArrivals'],

        'prob_triage_empty': prob_triage_empty,
        'prob_beds_empty': prob_beds_empty,
        'prob_both_empty': prob_both_empty,

        'avg_nurse_util': avg_nurse_util,
        'avg_occupied_beds': avg_occupied_beds,

        'critical_arrivals': state['criticalCount'],
        'rejected_critical': state['rejectedCritical'],
        'crit_reject_rate': crit_reject_rate,

        'stable_count': state['stableCount'],
        'prop_treated_home': prop_home,

        'avg_time_in_system': avg_time_sys,
    }

    return event_history, results


# ===============================
# EXAMPLE: RUN & PRINT
# ===============================
if __name__ == "__main__":
    # Example: let's do 20 healed, with 'full' initial condition
    random.seed(SEED)
    ev_hist, stats = run_simulation(target_healed=200, max_events=9999999, initial_condition='full')

    print("First 20 events (or fewer):")
    for row in ev_hist:
        print(row)

    print("\nFinal Stats:")
    for k,v in stats.items():
        print(f"{k}: {v}")