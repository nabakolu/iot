(define (problem windows)
    (:domain awp)
    (:objects
        window1 - window
        window1noise - noise

        blinds1 -blind
        blinds2 -blind
        blinds3 -blind

        co2state - co2
        centralheating - heater
    )
    (:init
        (= (openedblinds) 0)
        (closed window1)
        (too_high co2state)
        (high_noise window1 window1noise)

        (open blinds1)
        ; (closed blinds2)
        ; (closed blinds3)

        (blinding blinds1)
        (blinding_initial blinds1)
        ; (not_blinding blinds2)
        ; (not_blinding blinds3)

        
        ; (not_blinding_initial blinds2)
        ; (not_blinding_initial blinds3)

    )
    (:goal
        (and
            (ok co2state)
            (not_blinding blinds1)
            (or (and((blinding_initial blinds1) (closed blinds1)) and((not_blinding_initial blinds1) (open blinds1))))
            ; (not_blinding blinds2)
            ; (not_blinding blinds3)
        )
    )
    (:metric maximize (openedblinds))
)