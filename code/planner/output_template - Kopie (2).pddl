(define (problem windows)
    (:domain awp)
    (:objects
 window_west window_east - window
 blind_east blind_west - blind
central_heater - heater

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
(= (co2) 0)
(closed window_west)
(action_available window_west)
(= (wind window_west) 0.07200000000000001)
(= (ambientnoise window_west) 1)
(= (rain window_west) 0.0)
(closed window_east)
(action_available window_east)
(= (wind window_east) 0)
(= (ambientnoise window_east) 0)
(= (rain window_east) 0.0)
(open blind_east)
(not_blinding blind_east)
(not_blinding_initial blind_east)
(open blind_west)
(not_blinding blind_west)
(not_blinding_initial blind_west)
(heater_action_available central_heater)
(heater_on central_heater)
(= (min_temp central_heater) 17)
(= (curr_temp central_heater) 22.48)
(= (temperatureDiffMinimum central_heater) -5.48)
(= (temperatureDiffOutside central_heater) 2.5599999999999987)

        
    )
    (:goal
        
(and
(not_blinding blind_east)
(preference blindsOpen
  (open blind_east)
)
(not_blinding blind_west)
(preference blindsOpen
  (open blind_west)
)
(preference windowsOpen
  (open window_west)
)
(preference windowsOpen
  (open window_east)
)
(preference heaterPref
  (heater_off central_heater)
)
(preference heaterPref
  (heater_on central_heater)
)
)

        
    )
    (:metric maximize (+ (blindsmetric) (+ (co2metric) (heaterweight))))
)