(define (problem windows)
    (:domain awp)
    (:objects
        window1 window2 window3 - window
        window1noise - noise
        blind1 blind2 blind3 - blind
        co2state - co2
        centralheating - heater
    )
    (:init
        (= (openedblinds) 5)
        (= (co2value) 5)
        (not_perfect co2state)
        ;win1 (should close)
        (closed window1)
        (= (ambientnoise window1) 2)
        (action_available window1)
        ;(high_noise window1 window1noise)

        ;win2 
        (closed window2)
        (= (ambientnoise window2) 2)
        (action_available window2)

        ;win3 
        (open window3)
        (= (ambientnoise window3) 2)
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

        ; (closed blinds3)

        
        ;(blinding_initial blinds2)
       
        ; (not_blinding blinds3)

        
        
        ; (not_blinding_initial blinds3)

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
        )
    )
    (:metric maximize (+ (openedblinds) (co2value)))
)