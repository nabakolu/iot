## AI Planning component

`ai_planning_orchestration.py` is the entrypoint to the AI Planning component and uses the pddl templates and optic-clp to generate a problem and calculate a solution and
then calls the plan execution component.

## Plan Execution component

`execute_solution.py` contains a method to parse output from optic-clp and send command messages to actuators.

## Examples for generated problems

The examples folder contains example problem files that were generated with different system settings and environments.


