(define (domain awp)
(:requirements :strips :typing :fluents)
(:types 
    actuator heater co2 sensorstate - object
    window blind - actuator
    noise wind rain light - sensorstate
)

(:predicates (open ?w - actuator)
            (closed ?w - actuator)
            (off ?h - heater)
            (middle ?h - heater)
            (high ?h - heater)
            (too_high ?c - co2)
            (ok ?c - co2)
            (temp_too_low ?t - heater)
            (temp_too_high ?t - heater)
            (high_noise ?w - window ?n - noise)
            (low_noise ?w - window ?n - noise)
            (blinding ?w - blind)
            (not_blinding ?w - blind)
            (not_blinding_initial ?w - blind)
            (blinding_initial ?w - blind)
            )

(:functions
    (openedblinds)
)

(:action openwindow
:parameters (?window - window ?co2 - co2 ?noise - noise)
:precondition (and (closed ?window)
                (too_high ?co2)
                (high_noise ?window ?noise)
)
:effect  (and (not(too_high ?co2)) 
                (ok ?co2)
                (open ?window)
                (not(closed ?window))
))

(:action closewindow
:parameters (?window - window ?co2 - co2 ?noise - noise)
:precondition (and (open ?window)
                    (too_high ?co2)
                    )
:effect  (and   (closed ?window)
                (not(open ?window))
                (not(high_noise ?window ?noise))
                (low_noise ?window ?noise)
))

(:action openblinds
:parameters (?blind - blind)
:precondition (and (closed ?blind)
                    (not_blinding_initial ?blind)
)
:effect  (and   (open ?blind)
                (increase (openedblinds) 1)
))

(:action closeblinds
:parameters (?blind - blind)
:precondition (and (blinding ?blind)
                    (open ?blind)
)
:effect  (and   (closed ?blind)
                (not(blinding ?blind))
                (not_blinding ?blind)
))
)


