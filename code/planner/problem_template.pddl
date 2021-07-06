(define (problem windows)
    (:domain awp)
    (:objects
;[objects-template-string]
        ; window1 window2 window3 - window
        ; window1noise - noise
        ; blind1 blind2 blind3 - blind
        ; co2state - co2
        ; heater1 - heater
    )
    (:init
        ;vars for weights and functions --> do not replace
        (= (blindsmetric) 0)
        (= (co2metric) 0)
        (= (heaterweight) 0)
        (= (any_window_open) 0)

;generated part
;[init-template-string]
        
    )
    (:goal
        
;[goal-template-string]
        
    )
    (:metric maximize (+ (blindsmetric) (+ (co2metric) (heaterweight))))
)