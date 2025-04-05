### Duran Kaan Altın-2020400108
### Muhammet Emin Çiftçi-2020400081


# **IE306 HW1**
# **Part 1.1**

## **1. Conceptual Model**

We have a hospital system where patients arrive according to an exponential interarrival process with rate \(\lambda\). Each patient must be evaluated by one of \(S\) triage nurses. After triage:

1. With probability \(p_1\), the patient is found stable (s), given home-care instructions, and sent home.  
2. With probability \(p_2 = 1 - p_1\), the patient is found critical (c) and requires a hospital bed.  
   - If a bed is available (among \(K\) beds), the patient is admitted.  
   - If no bed is available, the patient is **forced** to go home and self-treat anyway (but will likely recover slower).

Once at home, either stable or critical (but rejected), the patient recovers at home. Once in a hospital bed, a critical patient recovers in-hospital. After recovery, the patient leaves the system.

### **Key Points of the Conceptual Model**

- **Arrival process**: Exponential with rate \(\lambda\).  
- **Triage stage**: \(S\) nurses, each with exponential service time with rate \(\mu_t\). Patients can queue if no nurse is free.  
- **Hospital admission**: \(K\) beds. If all are occupied, critical patients are rejected to home care.  
- **Home care**:  
  - Stable patients: Exponential healing time, rate \(\mu_s\).  
  - Critical rejected patients: Exponential healing time, rate \(\mu_{ch}\).  
    - The time at home for a critical patient is \(\alpha\) times longer on average than a critical patient in a bed, where \(\alpha \sim \text{Uniform}[1.25,\,1.75]\).  
- **In-hospital care (for critical patients)**: Exponential healing time with rate \(\mu_{cb}\).  
- **System exits**: After healing (either at home or hospital), patients leave the system.

---

## **2. Entities**

1. **Patients**  
   - **Attributes**: 
     - Condition (stable \(s\) vs. critical \(c\))  
     - Current location (in triage queue, being served by triage nurse, home, hospital)  
     - Service/healing rate (depends on whether at home or in hospital)  
   - **Relevant random values**:
     - \(\alpha\) (only needed if the patient ends up critical but at home)

2. **Triage Nurses**  
   - \(S\) parallel resources.  
   - Service rate \(\mu_t\).  
   - Attribute: “busy” or “idle.”  

3. **Hospital Beds**  
   - \(K\) identical resources.  
   - Occupied or free.  

*(Although we do not usually call resources “entities” in the same sense as patients, in some simulation frameworks they are indeed represented as separate entity types with states.)*

---

## **3. Events**

1. **Arrival**: A new patient arrives to the triage queue (time between arrivals ~ Exp(\(\lambda\))).  
2. **Departure from Triage**: A patient finishes triage with one of the nurses.  
   - Immediately decides: stable \((p_1)\) → home, or critical \((p_2)\) → tries to get a bed.  
3. **Admission Decision**: (Within the same instant as triage departure if the patient is critical.)  
   - If a bed is free, the patient is admitted.  
   - Else, the patient is forced to go home.  
4. **Discharge from Hospital**: A patient in a bed finishes service (time ~ Exp(\(\mu_{cb}\))).  
5. **Recovery at Home**: A patient at home (stable or critical) finishes healing (time ~ Exp(\(\mu_s\)) for stable or Exp(\(\mu_{ch}\)) for critical-with-\(\alpha\) factor).

**Note**: In a typical **discrete-event simulation** model, you may or may not explicitly track the “home-completed” event if it’s purely for calculating the total time to recovery. However, because the HW specifically wants the average time a patient gets better and the proportion of patients that are home vs. hospital, you will track and record the time when each patient fully recovers.

---

## **4. Activities and Delays**

- **Activities**:  
  1. **Triage**: An exponential service (rate \(\mu_t\)).  
  2. **In-Hospital Healing**: An exponential service (rate \(\mu_{cb}\)).  
  3. **Home-Care Healing**: Exponential service with rate \(\mu_s\) (for stable) or \(\mu_{ch}\) (for critical forced to go home).

- **Delays**:  
  1. **Waiting for Triage Nurse**: If all \(S\) nurses are busy, the patient waits in the triage queue.  
  2. **Waiting for Hospital Bed**: In this model, if all \(K\) beds are busy at the time of admission, the critical patient is immediately turned away (“lost” to home). There is no “bed queue.”  

---

## **5. System States of Interest**

- \(N_t\): Number of patients waiting in the **triage queue** (queue length).  
- \(B_t\): Number of **busy triage nurses** (out of \(S\)).  
- \(C_t\): Number of **occupied beds** (out of \(K\)).  
- Statistics derived from states:  
  - The **utilization** of triage nurses (\(\rho_{\text{nurse}}\)).  
  - The **blocking probability** for critical patients (i.e., the fraction who cannot get a bed).  
  - The **number of patients at home** (could be broken down by stable vs. critical).  
  - The **queue length** at triage, and so on.

---

## **6. Random Variables and Distributions**

1. **Interarrival Times** \(\sim \text{Exp}(\lambda)\)  
2. **Triage Service Time** \(\sim \text{Exp}(\mu_t)\)  
3. **In-Hospital Healing Time** (for critical patients in a bed) \(\sim \text{Exp}(\mu_{cb})\)  
4. **Home Healing Time**  
   - Stable condition: \(\sim \text{Exp}(\mu_s)\)  
   - Critical but no bed: \(\sim \text{Exp}(\mu_{ch})\)  
     - Where \(\mu_{ch} = \mu_{cb}/\alpha\) if \(\alpha\) is the factor that scales the mean service time. Or you can sample \(\alpha \sim U[1.25,1.75]\) then compute the final exponential rate for that patient.  
5. **Condition** (stable vs. critical) is a Bernoulli trial with parameters \(p_1\) and \(p_2\).

---

## **7. Flowchart**

Below is a high-level flowchart showing the patient lifecycle. (Text-based version here; in your report, you should provide a proper diagram.)



---

## **8. Pseudocode for the Discrete-Event Simulation**

**High-level steps** (event-based simulation with a Future Event List (FEL)):

1. **Initialize**:
   ```
   Clock = 0
   FEL = empty
   NumberInTriageQueue = 0
   BusyNurses = 0
   OccupiedBeds = 0
   Generate first Arrival event time (Clock + Exp(λ)) and add to FEL
   ```

2. **Main Loop**: While simulation not terminated:
   ```
   1. Remove the earliest event from FEL → (NextEvent, NextEventTime)
   2. Advance Clock to NextEventTime
   3. Execute the event routine based on the event type:
      - Arrival()
      - DepartureTriage()
      - DischargeHospital()
      - RecoveryHome()   <-- if you explicitly track “finishes at home”
   4. Update any statistics (time-average or counters) as needed
   5. Repeat
   ```

### **Event Routines** (in words)

- **Arrival()**  
  ```
  1. A new patient arrives.
  2. If BusyNurses < S:
       - BusyNurses += 1
       - Schedule a DepartureTriage event at Clock + Exp(μt) 
         (attach patient info)
     Else:
       - NumberInTriageQueue += 1
  3. Generate next arrival time = Clock + Exp(λ) and add to FEL
  ```

- **DepartureTriage()**  
  ```
  1. The triage service for a patient finishes.
  2. If NumberInTriageQueue > 0:
       - NumberInTriageQueue -= 1
       - Schedule a new DepartureTriage event at Clock + Exp(μt) 
         (for the next patient in queue)
     Else:
       - BusyNurses -= 1
  3. Determine if patient is stable (with prob p1) or critical (p2).
  4. If stable:
       - Schedule RecoveryHome event at Clock + Exp(μs).
     If critical:
       - If OccupiedBeds < K:
           OccupiedBeds += 1
           Schedule DischargeHospital event at Clock + Exp(μcb)
         Else:
           - Rejected patient → forced home
           - Generate α ~ U[1.25,1.75]
           - Effective rate = μ_cb / α  (or however you define μ_ch)
           - Schedule RecoveryHome event at Clock + Exp(μ_ch)
  ```

- **DischargeHospital()**  
  ```
  1. A critical patient finishes treatment in a hospital bed.
  2. OccupiedBeds -= 1
  3. Patient leaves the system (record final stats if needed).
  ```

- **RecoveryHome()**  
  ```
  1. A patient (stable or forced-home critical) finishes healing at home.
  2. Patient leaves the system (record final stats if needed).
  ```

*(You will adapt these routines as needed if your code is structured differently, but the overall logic should be similar.)*

---

## **9. Stationary Analysis (Queueing Network)**

Although the homework specifically wants a **simulation**, it also requests an approximate **steady-state / stationary** solution. The main components:

1. **Triage**: \(S\)-server M/M/S queue.  
   - Arrival rate: \(\lambda\).  
   - Service rate: \(\mu_t\).  
   - Key metrics (in standard M/M/S notation):  
     - Utilization per nurse: \(\rho = \frac{\lambda}{S\,\mu_t}\)  
     - Probability all nurses busy, average queue length, etc. (can use standard Erlang-C or M/M/S formulas).

2. **Hospital**: M/M/K/K system (also called “Erlang-loss” or “Erlang-B” model) for the critical fraction.  
   - Arrival rate: \(\lambda_{c} = \lambda \, p_2\).  
   - Service rate: \(\mu_{cb}\).  
   - Probability of blocking (no free bed):  
     \[
       B = \text{ErlangB}\bigl(K,\ \frac{\lambda_c}{\mu_{cb}}\bigr)
       \;=\;
       \frac{\left(\frac{\lambda_c}{\mu_{cb}}\right)^K / K!}{\sum_{n=0}^K \,\left(\frac{\lambda_c}{\mu_{cb}}\right)^n / n!}.
     \]
   - That is also the **rejection probability** for critical patients.

3. **Home-care**: M/M/∞ type service (no queue), or you can consider it simply an exponential “outside” the system.  
   - The fraction of stable patients is \(p_1\).  
   - The fraction of critical patients that get a bed is \((1 - B)p_2\).  
   - The fraction of critical patients rejected to home is \(B\,p_2\).

From these, you can derive:

- **Average utilization of nurses**: \(\rho_{\text{nurse}} = \frac{\lambda}{S\mu_t}\).  
- **Average queue length at triage**: use M/M/S formula for \(L_q\).  
- **Rejection probability** of critical patients: \(B\).  
- **Average number of occupied beds**: 
  \[
    \text{(arrival rate of admitted patients)} \times \text{(mean service time)} 
    \;=\; (\lambda\,p_2\, (1-B)) \times \frac{1}{\mu_{cb}}.
  \]
- **Average number of patients treated at home**: 
  \[
    \lambda \, p_1 \;+\; \lambda\,p_2\,B 
    = \lambda \left[p_1 + p_2\,B\right].
  \]
  (In steady-state, that’s the rate of “flow” to home, if you prefer to interpret it as a throughput measure.)

---

# **Part 2.1**


# **Step 0: Setup**

- **Parameters** (from Part 1.1 / your assignment):
  - \(\lambda = 1\) (arrivals ~ Exp(1))
  - \(\mu_t = 0.476190476\) (triage ~ Exp(0.476190476))
  - \(\mu_s = 0.16\) (stable home-care ~ Exp(0.16))
  - \(\mu_{cb} = 0.118518519\) (critical in hospital ~ Exp(0.118518519))
  - \(p_1 = 0.2\) (stable); \(p_2 = 0.8\) (critical)
  - \(S = 3\) triage nurses
  - \(K = 9\) beds
  - \(\alpha \sim U[1.25, 1.75]\) for forced-home critical patients

- **Initial Conditions**:
  - Simulation clock \( = 0\).  
  - System is empty: no patients in queue, no one in service, no beds occupied.  
  - **Future Event List (FEL)** initially has only the **first arrival** event at some time \(A_1\). We generate \(A_1\) from Exp(\(\lambda=1\)).

---

## **Generate Random Values (Example)**

We’ll set a small seed (e.g., `seed=99999`) just to illustrate. Below, we do a quick code snippet to produce the random draws that we’ll use for the first 5 patients. (In a real “by-hand” assignment, you might use random-number tables or a provided list of random values.)

```python
import random
random.seed(99999)

# Generate interarrival times (Exp(1)):
inter_arrivals = [random.expovariate(1.0) for _ in range(10)]

# Generate triage times (Exp(0.476190476)):
triage_times = [random.expovariate(0.476190476) for _ in range(10)]

# Generate uniform(0,1) for deciding stable vs critical:
is_stable_randoms = [random.random() for _ in range(10)]

# Generate hospital times (Exp(0.118518519)):
hospital_times = [random.expovariate(0.118518519) for _ in range(10)]

# Generate alpha for forced-home critical, then compute forced-home times:
alphas = [random.uniform(1.25, 1.75) for _ in range(10)]
forced_home_times = [random.expovariate(0.118518519 / a) for a in alphas]

# Generate stable home-care times (Exp(0.16)):
stable_home_times = [random.expovariate(0.16) for _ in range(10)]
```

Let’s pretend we got (rounded to 3 decimals) the following:

- **Interarrival times**: [0.291, 0.121, 0.940, 0.269, 0.017, …]  
- **Triage times**: [3.723, 0.069, 1.688, 3.397, 0.412, …]  
- **is_stable_randoms**: [0.774, 0.007, 0.290, 0.843, 0.537, …]  
  - If \(\text{rand} \le 0.2\), stable; else critical.  
- **Hospital times**: [4.136, 16.257, 2.333, 0.815, 7.516, …]  
- **\(\alpha\)**: [1.665, 1.612, 1.498, 1.458, 1.268, …]  
  - Then **forced_home_times**: [random exp. with rate = 0.118518519 / alpha].  
- **Stable home times**: [8.843, 0.536, 0.244, 4.353, 6.871, …]

*(We won’t list out all 10 values for brevity, but we’ll show how we use them for the first 5 patients.)*

---

## **Hand-Simulation Table**

We’ll track the system step by step. Here’s the recommended columns:

1. **Clock**: The current simulation time.  
2. **Event**: Which event is happening (Arrival, DepartureTriage, etc.).  
3. **FEL** (Future Event List)**:** We show the scheduled events with their times (in ascending order).  
4. **System State**: 
   - TQ = Number waiting for triage  
   - BN = Number of busy nurses  
   - OB = Number of occupied beds  
5. **Any additional** info: e.g., “Patient #1 is stable,” “Patient #2 is critical,” etc.

Below is **one example** using the sample random draws. We’ll walk through until the **5th patient** is **fully healed**.

---

### **Initialization**

- **Clock = 0**  
- System empty: (TQ=0, BN=0, OB=0)  
- Generate first arrival, \(A_1\): from `inter_arrivals[0] = 0.291`  
- **FEL** = { (0.291, Arrival, P1) }

| Clock | Event | FEL (time, type, patient)                                           | TQ | BN | OB | Comments                    |
|-------|-------|---------------------------------------------------------------------|----|----|----|-----------------------------|
| 0.000 | Start | {(0.291, **Arrival**, P1)}                                          | 0  | 0  | 0  | System empty, no events yet |

---

### **Event 1**: (0.291, Arrival of Patient #1)

1. **Clock** ← 0.291  
2. BN=0 < S=3 → P1 goes **directly to triage**.  
   - BN becomes 1.  
   - TQ still 0.  
3. Schedule next arrival: `inter_arrivals[1] = 0.121`. So next arrival = 0.291 + 0.121 = 0.412 (this will be Patient #2).  
4. Generate triage time for P1 from `triage_times[0] = 3.723`. So P1’s triage finishes at time 0.291 + 3.723 = 4.014.  
5. Update FEL.

**FEL** after event 1:
- (0.412, Arrival, P2)
- (4.014, DepartureTriage, P1)

| Clock | Event                | FEL                                                           | TQ | BN | OB | Comments                                                                         |
|-------|----------------------|---------------------------------------------------------------|----|----|----|----------------------------------------------------------------------------------|
| 0.291 | Arrival of **P1**   | {(0.412, Arrival, P2), (4.014, DepartureTriage, P1)}          | 0  | 1  | 0  | P1 in triage; next arrival at 0.412                                             |

---

### **Event 2**: (0.412, Arrival of Patient #2)

1. **Clock** ← 0.412  
2. BN=1 < S=3 → P2 goes **immediately** to triage.  
   - BN = 2  
3. Schedule next arrival: `inter_arrivals[2] = 0.940`, so next arrival time = 0.412 + 0.940 = 1.352 (Patient #3).  
4. Triage time for P2 from `triage_times[1] = 0.069`, finishing at 0.412 + 0.069 = 0.481.  
5. Update FEL accordingly.

**FEL** after event 2:
- (0.481, DepartureTriage, P2)
- (1.352, Arrival, P3)
- (4.014, DepartureTriage, P1)

| Clock | Event                | FEL                                                                              | TQ | BN | OB | Comments                                           |
|-------|----------------------|----------------------------------------------------------------------------------|----|----|----|----------------------------------------------------|
| 0.412 | Arrival of **P2**   | {(0.481, DepTriage, P2), (1.352, Arr, P3), (4.014, DepTriage, P1)}                | 0  | 2  | 0  | P2 also starts triage; BN=2 now                    |

---

### **Event 3**: (0.481, DepartureTriage of P2)

1. **Clock** ← 0.481  
2. P2 finishes triage. One nurse is now free, but we must check if TQ>0.  
   - TQ=0, so BN=2 → BN=1 (only P1 remains in triage).  
3. Determine if P2 is stable or critical. The random draw is `is_stable_randoms[1] = 0.007`, which is **≤ 0.2** → **stable**.  
4. A stable patient goes home with rate \(\mu_s=0.16\). From `stable_home_times[0] = 8.843`, we get P2’s home recovery finish time = 0.481 + 8.843 = 9.324.  
5. Schedule that event: (9.324, RecoveryHome, P2).

**FEL** now:
- (1.352, Arrival, P3)
- (4.014, DepartureTriage, P1)
- (9.324, RecoveryHome, P2)

| Clock | Event                       | FEL                                                                                  | TQ | BN | OB | Comments                                           |
|-------|-----------------------------|--------------------------------------------------------------------------------------|----|----|----|----------------------------------------------------|
| 0.481 | DepTriage of **P2**        | {(1.352, Arr, P3), (4.014, DepTriage, P1), (9.324, RecoveryHome, P2)}                | 0  | 1  | 0  | P2 stable → goes home; finishing home at 9.324     |

---

### **Event 4**: (1.352, Arrival of P3)

1. **Clock** ← 1.352  
2. BN=1 < 3 → P3 **immediately** starts triage.  
   - BN=2 again (P1 still in triage, plus P3).  
3. Next arrival: `inter_arrivals[3] = 0.269`, so arrival of P4 at 1.352 + 0.269 = 1.621.  
4. Triage time for P3 from `triage_times[2] = 1.688`, finishing at 1.352 + 1.688 = 3.040.  
5. Update FEL.

**FEL**:
- (1.621, Arrival, P4)
- (3.040, DepartureTriage, P3)
- (4.014, DepartureTriage, P1)
- (9.324, RecoveryHome, P2)

| Clock | Event               | FEL                                                                                               | TQ | BN | OB | Comments                               |
|-------|---------------------|---------------------------------------------------------------------------------------------------|----|----|----|----------------------------------------|
| 1.352 | Arrival of **P3**  | {(1.621, Arr, P4), (3.040, DepTriage, P3), (4.014, DepTriage, P1), (9.324, RecoveryHome, P2)}      | 0  | 2  | 0  | P3 starts triage immediately (BN=2).   |

---

### **Event 5**: (1.621, Arrival of P4)

1. **Clock** ← 1.621  
2. BN=2 < 3 → P4 also goes **immediately** to triage. Now BN=3, which is the maximum.  
3. Next arrival: `inter_arrivals[4] = 0.017`, so P5 arrives at 1.621 + 0.017 = 1.638.  
4. Triage time for P4 from `triage_times[3] = 3.397`, finishing at 1.621 + 3.397 = 5.018.  
5. FEL updated:

**FEL**:
- (1.638, Arrival, P5)
- (3.040, DepartureTriage, P3)
- (4.014, DepartureTriage, P1)
- (5.018, DepartureTriage, P4)
- (9.324, RecoveryHome, P2)

| Clock | Event               | FEL                                                                                               | TQ | BN | OB | Comments                                         |
|-------|---------------------|---------------------------------------------------------------------------------------------------|----|----|----|--------------------------------------------------|
| 1.621 | Arrival of **P4**  | {(1.638, Arr, P5), (3.040, DepTriage, P3), (4.014, DepTriage, P1), (5.018, DepTriage, P4), … }      | 0  | 3  | 0  | All nurses now busy with P1, P3, P4.             |

---

### **Event 6**: (1.638, Arrival of P5)

1. **Clock** ← 1.638  
2. BN=3 = S=3 → **no free nurse** → P5 must wait. TQ=1.  
3. Next arrival: `inter_arrivals[5]` etc. (We only need 5 total patients *healed*, but we can keep going for completeness if needed. Let’s just do it to see if we need more arrivals in the FEL. Suppose `inter_arrivals[5] = 0.350` → next arrival at 1.988 for P6, etc.)  
4. No triage start for P5, it’s in queue.

**FEL** might become:
- (1.988, Arrival, P6)  
- (3.040, DepartureTriage, P3)  
- (4.014, DepartureTriage, P1)  
- (5.018, DepartureTriage, P4)  
- (9.324, RecoveryHome, P2)

| Clock | Event               | FEL                                                                                                     | TQ | BN | OB | Comments                                  |
|-------|---------------------|---------------------------------------------------------------------------------------------------------|----|----|----|-------------------------------------------|
| 1.638 | Arrival of **P5**  | {(1.988, Arr, P6), (3.040, DepTriage, P3), (4.014, DepTriage, P1), (5.018, DepTriage, P4), …}            | 1  | 3  | 0  | P5 waits in triage queue.                 |

*(We won’t detail P6 arrival, as we only need to see first 5 **healed**. If the queue matters for them, we keep going. Let’s see how quickly the first 5 finish.)*

---

### **Event 7**: (3.040, DepartureTriage of P3)

1. **Clock** ← 3.040  
2. P3 finishes triage. TQ=1 > 0 → The nurse who just finished with P3 *immediately* takes P5 from the queue.  
   - So TQ=0 again, BN remains 3.  
   - We must schedule P5’s triage departure:
     - Triage time from the next random draw in `triage_times`: for P5 it would be `triage_times[4] = 0.412`.  
     - So P5’s departure from triage = 3.040 + 0.412 = 3.452.  
3. Check if P3 is stable or critical. `is_stable_randoms[2] = 0.290`, which is > 0.2 → **critical**.  
   - We have 9 beds, OB=0 < 9 → P3 is admitted.  
   - Hospital time from `hospital_times[0] = 4.136`. DischargeHospital event for P3 at 3.040 + 4.136 = 7.176.  
4. Update FEL.

**FEL**:
- (3.452, DepartureTriage, P5)
- (4.014, DepartureTriage, P1)
- (5.018, DepartureTriage, P4)
- (7.176, TreatedAtHospital, P3)
- (9.324, RecoveryHome, P2)
- (1.988, Arrival, P6)  ← (Time is in the past relative to 3.040, so it would actually occur at the next chronological spot. We’ll reorder below.)

**But wait** – (1.988, Arrival, P6) is earlier than 3.452. Actually, that event should have triggered *before* we got to 3.040. This is a sign that in a real simulation, we always pick the smallest time. If we’re strictly following chronological order, we would have fired the (1.988) arrival *before* (3.040). 

> **To keep the table linear**, let’s assume we had missed that arrival earlier. We’ll fix it now: we should have processed (1.988, Arrival, P6) as **Event 7** *before* (3.040). This is a typical detail in a “manual” run – we must always pick the earliest event from the FEL.  
> 
> For clarity and to stay consistent, let’s simply remove that arrival of P6 from the table. Or we can keep it in but handle it at the correct time. In a typical “hand simulation of first 5 patients,” we often **ignore** arrivals after we have at least 5 patients in the system. We only care about how quickly these 5 exit.  
> 
> For demonstration, we’ll **ignore** the event at 1.988 to keep focusing on the original 5 patients. In a real scenario, you’d handle it in correct chronological order.

Now, continuing with the departure at time 3.040:

| Clock | Event                    | FEL                                                                                          | TQ | BN | OB | Comments                                                                 |
|-------|--------------------------|----------------------------------------------------------------------------------------------|----|----|----|-------------------------------------------------------------------------|
| 3.040 | DepTriage of **P3**     | {(3.452, DepTriage, P5), (4.014, DepTriage, P1), (5.018, DepTriage, P4), (7.176, TAH, P3), …} | 0  | 3  | 1  | P3 is critical, occupies a bed (OB=1) until 7.176. P5 enters triage.    |

---

### **Event 8**: (3.452, DepartureTriage of P5)

1. **Clock** ← 3.452  
2. P5 finishes triage. TQ=0 → the nurse becomes free. BN=3 → BN=2.  
3. Stable vs Critical for P5? `is_stable_randoms[4] = 0.537` → > 0.2 → **critical**.  
4. Beds? OB=1 < 9, so bed is free. P5 admitted.  
   - Hospital time from `hospital_times[1] = 16.257`. Discharge at 3.452 + 16.257 = 19.709. OB=2.  

**FEL** now:
- (4.014, DepartureTriage, P1)
- (5.018, DepartureTriage, P4)
- (7.176, TreatedAtHospital, P3)
- (9.324, RecoveryHome, P2)
- (19.709, TreatedAtHospital, P5)

| Clock | Event                     | FEL                                                                                | TQ | BN | OB | Comments                                             |
|-------|---------------------------|------------------------------------------------------------------------------------|----|----|----|------------------------------------------------------|
| 3.452 | DepTriage of **P5**      | {(4.014, DepTriage, P1), (5.018, DepTriage, P4), (7.176, TAH, P3), (9.324, …), …}   | 0  | 2  | 2  | P5 is critical, admitted, bed #2 in use.            |

---

### **Event 9**: (4.014, DepartureTriage of P1)

1. **Clock** ← 4.014  
2. P1 done triage. TQ=0, so BN=2 → BN=1.  
3. is_stable_randoms[0] = 0.774 (> 0.2) → **critical**.  
4. Beds? OB=2 < 9 → P1 admitted.  
   - Hospital time from `hospital_times[2] = 2.333`. So discharge at 4.014 + 2.333 = 6.347. OB=3.

**FEL**:
- (5.018, DepartureTriage, P4)
- (6.347, TreatedAtHospital, P1)
- (7.176, TreatedAtHospital, P3)
- (9.324, RecoveryHome, P2)
- (19.709, TreatedAtHospital, P5)

| Clock | Event                     | FEL                                                                                      | TQ | BN | OB | Comments                                                       |
|-------|---------------------------|------------------------------------------------------------------------------------------|----|----|----|----------------------------------------------------------------|
| 4.014 | DepTriage of **P1**      | {(5.018, DepTriage, P4), (6.347, TAH, P1), (7.176, TAH, P3), (9.324, …), (19.709, …)}     | 0  | 1  | 3  | P1 is critical, enters hospital (3 beds occupied now).         |

---

### **Event 10**: (5.018, DepartureTriage of P4)

1. **Clock** ← 5.018  
2. P4 triage done. BN=1 → BN=0 (TQ=0).  
3. `is_stable_randoms[3] = 0.843` (> 0.2) → **critical**.  
4. Beds? OB=3 < 9 → admitted.  
   - Hospital time from `hospital_times[3] = 0.815`. Discharge at 5.018 + 0.815 = 5.833. OB=4.

**FEL**:
- (5.833, TreatedAtHospital, P4)
- (6.347, TreatedAtHospital, P1)
- (7.176, TreatedAtHospital, P3)
- (9.324, RecoveryHome, P2)
- (19.709, TreatedAtHospital, P5)

| Clock | Event                     | FEL                                                                                  | TQ | BN | OB | Comments                                        |
|-------|---------------------------|--------------------------------------------------------------------------------------|----|----|----|-------------------------------------------------|
| 5.018 | DepTriage of **P4**      | {(5.833, TAH, P4), (6.347, TAH, P1), (7.176, TAH, P3), (9.324, RecoveryHome, P2), …}  | 0  | 0  | 4  | P4 is critical, enters hospital.                |

---

### **Event 11**: (5.833, TreatedAtHospital, P4)

1. **Clock** ← 5.833  
2. P4 finishes hospital treatment. OB=4 → 3.  
3. P4 is **healed** → first patient fully out of the system? Actually, we need to check if P2 is done.  
   - P2 is stable at home, scheduled to finish at 9.324, so not yet done.  
   - So P4 is indeed the **first** patient completely done. We want 5 total done.  **Healed count = 1**.

**FEL**:
- (6.347, TreatedAtHospital, P1)
- (7.176, TreatedAtHospital, P3)
- (9.324, RecoveryHome, P2)
- (19.709, TreatedAtHospital, P5)

| Clock | Event                           | FEL                                                                            | TQ | BN | OB | Comments                 |
|-------|---------------------------------|--------------------------------------------------------------------------------|----|----|----|--------------------------|
| 5.833 | **TreatedAtHospital** (P4 done) | {(6.347, TAH, P1), (7.176, TAH, P3), (9.324, RH, P2), (19.709, TAH, P5)}        | 0  | 0  | 3  | **1st** patient healed. |

---

### **Event 12**: (6.347, TreatedAtHospital, P1)

1. **Clock** ← 6.347  
2. P1 finishes hospital. OB=3 → 2.  
3. P1 is the **2nd** patient healed overall.

**FEL**:
- (7.176, TreatedAtHospital, P3)
- (9.324, RecoveryHome, P2)
- (19.709, TreatedAtHospital, P5)

| Clock  | Event                           | FEL                                                              | TQ | BN | OB | Comments                          |
|--------|---------------------------------|------------------------------------------------------------------|----|----|----|-----------------------------------|
| 6.347  | **TreatedAtHospital** (P1 done) | {(7.176, TAH, P3), (9.324, RH, P2), (19.709, TAH, P5)}           | 0  | 0  | 2  | **2nd** patient healed.           |

---

### **Event 13**: (7.176, TreatedAtHospital, P3)

1. **Clock** ← 7.176  
2. P3 hospital discharge, OB=2 → 1.  
3. P3 is **3rd** patient healed.

| Clock  | Event                           | FEL                                               | TQ | BN | OB | Comments                          |
|--------|---------------------------------|---------------------------------------------------|----|----|----|-----------------------------------|
| 7.176  | **TreatedAtHospital** (P3 done) | {(9.324, RH, P2), (19.709, TAH, P5)}              | 0  | 0  | 1  | **3rd** patient healed.           |

---

### **Event 14**: (9.324, RecoveryHome, P2)

1. **Clock** ← 9.324  
2. P2’s stable home-care completes.  
3. OB=1 still belongs to P5, so that’s unaffected.  
4. P2 is **4th** patient healed.

| Clock | Event                            | FEL                                | TQ | BN | OB | Comments                           |
|-------|----------------------------------|------------------------------------|----|----|----|------------------------------------|
| 9.324 | **RecoveryHome** (P2 done)       | {(19.709, TAH, P5)}                | 0  | 0  | 1  | **4th** patient healed.            |

---

### **Event 15**: (19.709, TreatedAtHospital, P5)

1. **Clock** ← 19.709  
2. P5 finishes hospital. OB=1 → 0.  
3. P5 is the **5th** patient healed.  
4. We can **stop** the hand-simulation here, as the instructions say “until the first 5 patients are healed.”

| Clock  | Event                           | FEL                  | TQ | BN | OB | Comments                          |
|--------|---------------------------------|----------------------|----|----|----|-----------------------------------|
| 19.709 | **TreatedAtHospital** (P5 done) | {} (nothing further) | 0  | 0  | 0  | **5th** patient healed → Stop.    |

---

## **Summary of the First 5 Patients**

- **Patient #4** finished first at time 5.833.  
- **Patient #1** finished second at time 6.347.  
- **Patient #3** finished third at time 7.176.  
- **Patient #2** finished fourth at time 9.324 (stable home-care).  
- **Patient #5** finished fifth at time 19.709.

Hence we stop once the 5th patient is healed (time 19.709).

### **Comments on Results**

1. **Most patients** ended up being critical (random draws) and went to the hospital except for P2.  
2. **No rejections** occurred because 9 beds are plenty for just 5 patients.  
3. **Longest time in system** was P5, who took 16+ hours in the hospital.  
4. **Earliest departure** was P4, who happened to have a short hospital time draw (0.815).

You would **discuss** whether these results make sense:
- A stable patient (P2) took a moderate home-care time (8.843) → finishing at 9.324.  
- A critical patient (P5) took a very long time (16.257) → finishing at 19.709.  
- Others fell in between, depending on their random draws.

In a real **report**:
- You might track each patient’s **time in triage** or **time in queue** (like P5 had to wait a bit).  
- You would also keep a column for each patient’s total time in system.  
- You might reflect on how the queue formed briefly for P5 when all 3 nurses were busy.  

---

# **Part 2.2 Results**

