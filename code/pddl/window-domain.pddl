(define (domain awp)
(:requirements :strips :typing :numeric-fluents :preferences)
(:types 
    actuator sensors - object
    window blind heater - actuator
    noise wind rain light co2 - sensors
)

(:predicates 
            ; actuator states
            (open ?w - actuator)
            (closed ?w - actuator)
            ; windows
            (action_available ?w - window)
            ; heater states
            (off ?h - heater)
            (middle ?h - heater)
            (high ?h - heater)
            (temp_too_low ?t - heater)
            (temp_too_high ?t - heater)
            ; co2 states
            (not_perfect ?c - co2)
            (ok ?c - co2)


            (high_noise ?w - window ?n - noise)
            (low_noise ?w - window ?n - noise)
            (blinding ?w - blind)
            (not_blinding ?w - blind)
            (not_blinding_initial ?w - blind)
            (blinding_initial ?w - blind)
            (test - window)
            )

(:functions
    ;ambient noise weight
    (ambientnoise ?w - window)
    ;misc
    (openedblinds)
    (outside_temp)
    (inside_temp)
    (co2value)
    ;(MaxCO2-currCO2)
    ;(windprevente+rainprevented+noiseprevented)
)

(:action openwindow
:parameters (?window - window ?co2 - co2)
:precondition (and ;(closed ?window)
                (not_perfect ?co2)
                (action_available ?window)
)
:effect  (and 
                (ok ?co2)
                (open ?window)
                (not(closed ?window))
                (not (action_available ?window))
                ;(assign (co2value) (- (co2value) (ambientnoise ?window)))
                (assign (co2value) (+ co2value (- 1 (ambientnoise ?window))))
))

(:action closewindow
:parameters (?window - window ?co2 - co2)
:precondition (and (open ?window) (action_available ?window))
:effect  (and   (closed ?window)
                (not(open ?window))
                (not (action_available ?window))
                (increase (co2value) 0.1)
                ; (not(high_noise ?window ?noise))
                ; (low_noise ?window ?noise)
))

(:action openblinds
:parameters (?blind - blind)
:precondition (and (closed ?blind)
                    (not_blinding_initial ?blind)
)
:effect  (and   (open ?blind)
                (not (closed ?blind))
                (increase (openedblinds) 1)
))

(:action closeblinds
:parameters (?blind - blind)
:precondition (and (blinding ?blind)
                    (open ?blind)
)
:effect  (and   (closed ?blind)
                (not (open ?blind))
                (not(blinding ?blind))
                (not_blinding ?blind)
))

; (:durative-action heating_high
;     :parameters (?heater - heater)
;     :duration (and (< ?duration 60) (> ?duration 0))
;     :condition ()
;     :effect (and 
;         (at start (and 
;         ))
;         (at end (and 
;         ))
;     )
; )

)


