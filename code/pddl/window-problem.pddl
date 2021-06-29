(define (problem windows)
    (:domain awp)
    (:objects
        window1 window2 window3 - window
        window1noise - noise
        blind1 blind2 blind3 - blind
        co2state - co2
        heater1 - heater
    )
    (:init
        (= (openedblinds) 0)
        (= (co2value) 0)
        (= (heaterweight) 0)
        (= (any_window_open) 0)
        (not_perfect co2state)
        ;win1 (should close)
        (closed window1)
        (= (ambientnoise window1) 0.2)
        (= (wind window1) 0.8)
        (= (rain window1) 0.4)
        (action_available window1)
        ;(high_noise window1 window1noise)

        ;win2 
        (closed window2)
        (= (ambientnoise window2) 0.5)
        (= (wind window2) 0.8)
        (action_available window2)

        ;win3 
        (closed window3)
        (= (ambientnoise window3) 0.5)
        (= (wind window3) 0.1)
        (action_available window3)

        ;blinds1 should close
        (open blind1)
        (blinding blind1)

        ;closed blinds2 should open
        (closed blind2)
        ; (not (open blind2))
        ; (not (blinding blind2))
        (not_blinding blind2)
        (not_blinding_initial blind2)
        ; (not (blinding_initial blind2))

        ;blinds3 should open
        (open blind3)
        (blinding blind3)

        ;heater
        (= (min_temp heater1) 21)
        (= (curr_temp heater1) 11)
        (= (outdoor_temp heater1) 10)
        (heater_off heater1)
        (heater_action_available heater1)
        

    )
    (:goal
        (and
            ;(ok co2state)
            (not_blinding blind1)
            (not_blinding blind2)
            (not_blinding blind3)
            ;(= (openedblinds) 7)
            ;(open blind2)
            (preference test
                (open blind1)
            )
            (preference test1
                (open blind2)
            )
            (preference test2
                (open blind3)
            )
            (preference co2
                (open window1)
            )
            (preference co2
                (open window2)
            )
            (preference heater
                (heater_on heater1)
            )
            (preference heater
                (heater_off heater1)
            )
        )
    )
    (:metric maximize (+ (openedblinds) (+ (co2value) (heaterweight))))
)