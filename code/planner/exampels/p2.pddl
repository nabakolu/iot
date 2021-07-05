(define (problem windows)
    (:domain awp)
    (:objects
        window_east window_west - window
        blind_east blind_west - blind
        central_heater - heater
    )
    (:init
        ;vars for weights and functions --> do not replace
        (= (openedblinds) 0)
        (= (co2value) 0)
        (= (heaterweight) 0)
        (= (any_window_open) 0)

        (closed window_east)
        (= (ambientnoise window_east) 0.2)
        (= (wind window_east) 0.1)
        (= (rain window_east) 0.4)
        (action_available window_east)

        ;win2 
        (closed window_west)
        (= (ambientnoise window_west) 0.5)
        (= (wind window_west) 0.1)
        (action_available window_west)

        ;blinds1 should close
        (open blind_east)
        (blinding blind_east)

        ;closed blinds2 should open
        (open blind_west)
        ; (not (open blind_west))
        ; (not (blinding blind_west))
        (blinding blind_west)
        ;(not_blinding_initial blind_west)
        ; (not (blinding_initial blind_west))

        ;heater
        (= (min_temp central_heater) 21)
        (= (curr_temp central_heater) 22)
        (= (outdoor_temp central_heater) 10)
        (heater_on central_heater)
        (heater_action_available central_heater)

    )
    (:goal
        (and
            ;(ok co2state)
            (not_blinding blind_east)
            (not_blinding blind_west)
            ;(= (openedblinds) 7)
            ;(open blind_west)
            (preference test
                (open blind_east)
            )
            (preference test1
                (open blind_west)
            )

            (preference co2
                (open window_east)
            )
            (preference co2
                (open window_west)
            )
            (preference heater
                (heater_on central_heater)
            )
            (preference heater
                (heater_off central_heater)
            )
        )
    )
    (:metric maximize
        (+ (openedblinds) (+ (co2value) (heaterweight)))
    )
)