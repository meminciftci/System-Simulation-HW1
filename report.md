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

## **Summary of Part 1.1**

1. **Conceptual Model**: We have identified the arrival process, triage, branching to home or hospital, possible rejection, and final healing.  
2. **Entities / Attributes**: Patients (and resources: triage nurses, beds).  
3. **Events / Activities / Delays**: Defined the main events, exponential service (triage, hospital, home), and waiting queues.  
4. **System States**: Number in queue, busy nurses, occupied beds.  
5. **Random Variables**: Interarrival, triage-time, hospital/home healing times, condition (s vs. c), and the uniform \(\alpha\).  
6. **Flowchart**: Illustrates the flow from arrival through triage to either home or hospital.  
7. **Pseudocode**: Provided the outline for a next-event simulation approach.  
8. **Stationary Analysis**: Summarized approximate formulas for M/M/S (triage) and M/M/K/K (hospital), plus the fraction of patients that go home.

With the conceptual model in place, you can now proceed to **Part 1.2** (coding the generator functions and process routines) and eventually to Parts 2.1 and 2.2 for the manual and full simulation work.