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
            (not_action_available ?w - window)
            ; heater
            (heater_action_available ?h - heater)
            (heater_off ?h - heater)
            (heater_on ?h - heater)
            ;blinds
            (blinding ?w - blind)
            (not_blinding ?w - blind)
            (not_blinding_initial ?w - blind)

)

(:functions
    ;ambient noise
    (ambientnoise ?w - window)
    ;wind
    (wind ?w - window)
    ;rain
    (rain ?w - window)
    ;co2 status
    (co2)
    ;heater target range
    (min_temp ?h - heater)
    (curr_temp ?h - heater)
    (temperatureDiffMinimum ?h - heater)
    (temperatureDiffOutside ?h - heater)
    ;checks if window is open
    (any_window_open)
    ;insentive earned by opening blinds
    (blindsmetric)
    ;for metric maximize
    (co2metric)
    ;value generated by using heaters
    (heaterweight)
    
)

(:action openwindow
:parameters (?window - window)
:precondition (and ;(closed ?window)
                (action_available ?window)
)
:effect  (and 
                (open ?window)
                (not(closed ?window))
                (not (action_available ?window))
                (not_action_available ?window)
                (assign (any_window_open) 1)
                ;(assign (co2metric) (- (co2metric) (ambientnoise ?window)))
            (assign
                (co2metric)
                (+ co2metric (- (co2) (+ (ambientnoise ?window) (+ (wind ?window) (rain ?window))))))
        ))

(:action turn_heater_on
    :parameters (?heater - heater)
    :precondition (and ;(heater_off ?heater)
                        (heater_action_available ?heater)
                        (< (curr_temp ?heater) (min_temp ?heater))
                        (forall (?w - window)
                            (not_action_available ?w)
                        )
    )
        :effect (and (not (heater_off ?heater))
            (heater_on ?heater)
            (not (heater_action_available ?heater))
            ; (assign
            ;     (heaterweight)
            ;     (+ (heaterweight) (- (min_temp ?heater)
            ;             (- (curr_temp ?heater) (* (any_window_open) (temperatureDiffOutside ?heater)))
            ;         ))
            (assign (heaterweight) (+ (heaterweight) (- (- (min_temp ?heater) (curr_temp ?heater)) (* (any_window_open) (temperatureDiffOutside ?heater)))))
                ;(min temp - current temp)-anywinopem*tempDiffoutside
    )
)

(:action turn_heater_off
    :parameters (?heater - heater)
    :precondition (and ;(heater_on ?heater)
                        (heater_action_available ?heater)
                        ;(and (< (min_temp ?heater) (curr_temp ?heater))
                        (forall (?w - window)
                            (not_action_available ?w)
                        )
                        
    )
    :effect (and (not (heater_on ?heater))
                (heater_off ?heater)
                (not (heater_action_available ?heater))
                (increase (heaterweight) 0.1)
                ;(assign (heaterweight) (+ (heaterweight) (* (any_window_open) (temperatureDiffOutside ?heater))))
    )
)


(:action closewindow
:parameters (?window - window)
:precondition (and ;(open ?window) 
                    (action_available ?window))
:effect  (and   (closed ?window)
                (not(open ?window))
                (not (action_available ?window))
                (increase (co2metric) 0.1)
                (not_action_available ?window)
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
                (increase (blindsmetric) 1)
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

